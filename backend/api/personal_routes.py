"""
Personal dashboard API routes for single-user deployment
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import asyncio

from ..models import DecisionContext, DecisionResult
from ..treasury.treasury_monitor import TreasuryMonitor
from ..treasury.alerts import TreasuryAlertManager, AlertLevel, AlertType
from ..memory_core.memory_aggregator import MemoryAggregator
from ..dashboard.agent_vitals import AgentVitals
from ..mcp_agent import MCPDeFiAgent


router = APIRouter(prefix="/api/personal", tags=["personal"])

# Initialize components
treasury_monitor = TreasuryMonitor()
alert_manager = TreasuryAlertManager()
memory_aggregator = MemoryAggregator()
agent = MCPDeFiAgent()


@router.get("/dashboard")
async def get_personal_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive dashboard data for personal use
    """
    try:
        # Get treasury metrics
        treasury_data = await treasury_monitor.get_dashboard_metrics()
        
        # Get agent state
        agent_state = await agent.get_agent_state()
        
        # Get memory insights
        memory_insights = await memory_aggregator.mem0_manager.get_memory_insights()
        
        # Get recent decisions
        recent_decisions = await _get_recent_decisions(limit=10)
        
        # Get active positions
        positions = await _get_active_positions()
        
        # Get performance metrics
        performance = await _get_performance_metrics()
        
        # Check for alerts
        alert_summary = alert_manager.get_alert_summary()
        
        return {
            "status": "success",
            "data": {
                "treasury": treasury_data,
                "agent_state": agent_state,
                "memory_insights": memory_insights,
                "recent_decisions": recent_decisions,
                "positions": positions,
                "performance": performance,
                "alerts": alert_summary,
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/treasury/summary")
async def get_treasury_summary() -> Dict[str, Any]:
    """
    Get detailed treasury information
    """
    try:
        summary = await treasury_monitor.get_dashboard_metrics()
        historical = await treasury_monitor.get_historical_metrics(days=30)
        optimization = treasury_monitor.get_cost_optimization_report()
        
        return {
            "current": summary,
            "historical": historical,
            "optimization": optimization
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/recent")
async def get_recent_decisions(limit: int = 20) -> Dict[str, Any]:
    """
    Get recent agent decisions with outcomes
    """
    try:
        decisions = await _get_recent_decisions(limit)
        
        # Add performance summary
        successful = sum(1 for d in decisions if d.get('outcome', {}).get('success', False))
        
        return {
            "decisions": decisions,
            "summary": {
                "total": len(decisions),
                "successful": successful,
                "failed": len(decisions) - successful,
                "success_rate": successful / len(decisions) if decisions else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-strategy")
async def execute_strategy(strategy_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Manually trigger a specific strategy
    """
    try:
        # Create context for decision
        context = DecisionContext(
            current_treasury=treasury_monitor.manager.get_balance(),
            market_condition="manual",
            available_protocols=["aave", "compound", "curve"],
            gas_price=15.0,  # Could fetch real gas price
            risk_tolerance=parameters.get("risk_tolerance", 0.5) if parameters else 0.5
        )
        
        # Force specific strategy
        context.preferred_strategy = strategy_name
        
        # Execute decision
        decision = await agent.decide(context)
        
        return {
            "status": "executed",
            "decision": decision.dict(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop")
async def emergency_stop() -> Dict[str, Any]:
    """
    Emergency stop - halt all agent activities
    """
    try:
        # Create emergency alert
        await alert_manager.create_alert(
            AlertType.UNUSUAL_ACTIVITY,
            AlertLevel.EMERGENCY,
            "Emergency stop triggered by user",
            {"triggered_at": datetime.now().isoformat()}
        )
        
        # Set agent to HOLD mode
        agent.emergency_mode = True
        
        # Cancel any pending operations
        # TODO: Implement operation cancellation
        
        return {
            "status": "stopped",
            "message": "Agent activities halted. Manual restart required.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart-agent")
async def restart_agent() -> Dict[str, Any]:
    """
    Restart agent after emergency stop
    """
    try:
        # Clear emergency mode
        agent.emergency_mode = False
        
        # Clear critical alerts
        for alert_id in alert_manager.active_alerts:
            alert_manager.acknowledge_alert(alert_id)
        
        return {
            "status": "restarted",
            "message": "Agent restarted successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/summary")
async def get_performance_summary(days: int = 7) -> Dict[str, Any]:
    """
    Get performance summary for specified period
    """
    try:
        summary = await memory_aggregator.get_performance_summary(days)
        
        return {
            "period_days": days,
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/active")
async def get_active_alerts() -> Dict[str, Any]:
    """
    Get all active alerts
    """
    try:
        alerts = alert_manager.get_active_alerts()
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "requires_action": any(a['level'] in ['CRITICAL', 'EMERGENCY'] for a in alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> Dict[str, Any]:
    """
    Acknowledge an alert
    """
    try:
        success = alert_manager.acknowledge_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "status": "acknowledged",
            "alert_id": alert_id,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates
    """
    await websocket.accept()
    
    try:
        while True:
            # Send dashboard update every 5 seconds
            dashboard_data = await get_personal_dashboard()
            
            await websocket.send_json({
                "type": "dashboard_update",
                "data": dashboard_data["data"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Check for critical alerts
            alerts = alert_manager.get_active_alerts(AlertLevel.CRITICAL)
            if alerts:
                await websocket.send_json({
                    "type": "critical_alert",
                    "alerts": alerts,
                    "timestamp": datetime.now().isoformat()
                })
            
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        print("Dashboard WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


# Helper functions

async def _get_recent_decisions(limit: int) -> List[Dict[str, Any]]:
    """Get recent decisions from memory"""
    
    # Query recent decisions from Mem0
    all_memories = await memory_aggregator.mem0_manager.memory.get_all(
        user_id="personal",
        limit=limit
    )
    
    decisions = []
    for memory in all_memories:
        try:
            if memory.get('metadata', {}).get('type') == 'decision':
                content = json.loads(memory['memory'])
                decisions.append(content)
        except:
            continue
    
    return decisions


async def _get_active_positions() -> List[Dict[str, Any]]:
    """Get current active positions"""
    
    # This would integrate with blockchain to get real positions
    # For now, return mock data
    return [
        {
            "protocol": "aave",
            "asset": "USDC",
            "amount": 500,
            "apy": 0.05,
            "value_usd": 500,
            "opened_at": (datetime.now() - timedelta(days=3)).isoformat()
        }
    ]


async def _get_performance_metrics() -> Dict[str, Any]:
    """Calculate performance metrics"""
    
    # Get historical data
    decisions = await _get_recent_decisions(100)
    
    # Calculate metrics
    total_decisions = len(decisions)
    successful = sum(1 for d in decisions if d.get('outcome', {}).get('success', False))
    
    total_profit = sum(
        d.get('outcome', {}).get('profit_loss', 0) 
        for d in decisions 
        if d.get('outcome')
    )
    
    return {
        "total_decisions": total_decisions,
        "success_rate": successful / total_decisions if total_decisions > 0 else 0,
        "total_profit_loss": total_profit,
        "average_confidence": sum(d.get('decision', {}).get('confidence', 0) for d in decisions) / total_decisions if total_decisions > 0 else 0,
        "most_used_protocol": _get_most_used_protocol(decisions)
    }


def _get_most_used_protocol(decisions: List[Dict]) -> Optional[str]:
    """Find most frequently used protocol"""
    
    protocol_counts = {}
    for d in decisions:
        protocol = d.get('decision', {}).get('protocol')
        if protocol:
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
    
    if protocol_counts:
        return max(protocol_counts, key=protocol_counts.get)
    
    return None