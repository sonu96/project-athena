"""
Automation API routes for scheduled tasks and triggers
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, time
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..models import DecisionContext
from ..mcp_agent import MCPDeFiAgent
from ..treasury.treasury_monitor import TreasuryMonitor
from ..memory_core.memory_aggregator import MemoryAggregator


router = APIRouter(prefix="/api/automation", tags=["automation"])

# Initialize scheduler
scheduler = AsyncIOScheduler()
scheduler.start()

# Components
agent = MCPDeFiAgent()
treasury_monitor = TreasuryMonitor()
memory_aggregator = MemoryAggregator()

# Store active automations
active_automations = {}


@router.post("/schedule/treasury-check")
async def schedule_treasury_check(
    hour: int = 9,
    minute: int = 0,
    enabled: bool = True
) -> Dict[str, Any]:
    """
    Schedule daily treasury health check
    """
    job_id = "daily_treasury_check"
    
    try:
        # Remove existing job if any
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        if enabled:
            # Schedule the job
            scheduler.add_job(
                _check_treasury_health,
                CronTrigger(hour=hour, minute=minute),
                id=job_id,
                name="Daily Treasury Health Check",
                replace_existing=True
            )
            
            active_automations[job_id] = {
                "type": "treasury_check",
                "schedule": f"Daily at {hour:02d}:{minute:02d}",
                "enabled": True,
                "last_run": None
            }
            
            return {
                "status": "scheduled",
                "job_id": job_id,
                "schedule": f"Daily at {hour:02d}:{minute:02d}"
            }
        else:
            if job_id in active_automations:
                del active_automations[job_id]
            
            return {
                "status": "disabled",
                "job_id": job_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/market-scan")
async def schedule_market_scan(
    interval_hours: int = 4,
    enabled: bool = True
) -> Dict[str, Any]:
    """
    Schedule periodic market opportunity scan
    """
    job_id = "market_scan"
    
    try:
        # Remove existing job if any
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        if enabled:
            # Schedule the job
            scheduler.add_job(
                _scan_market_opportunities,
                'interval',
                hours=interval_hours,
                id=job_id,
                name="Market Opportunity Scan",
                replace_existing=True
            )
            
            active_automations[job_id] = {
                "type": "market_scan",
                "schedule": f"Every {interval_hours} hours",
                "enabled": True,
                "last_run": None
            }
            
            return {
                "status": "scheduled",
                "job_id": job_id,
                "schedule": f"Every {interval_hours} hours"
            }
        else:
            if job_id in active_automations:
                del active_automations[job_id]
            
            return {
                "status": "disabled",
                "job_id": job_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/rebalancing")
async def schedule_rebalancing(
    hour: int = 14,
    enabled: bool = True,
    threshold_percent: float = 10.0
) -> Dict[str, Any]:
    """
    Schedule daily portfolio rebalancing check
    """
    job_id = "daily_rebalancing"
    
    try:
        # Remove existing job if any
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        if enabled:
            # Schedule the job
            scheduler.add_job(
                _check_rebalancing,
                CronTrigger(hour=hour, minute=0),
                args=[threshold_percent],
                id=job_id,
                name="Daily Rebalancing Check",
                replace_existing=True
            )
            
            active_automations[job_id] = {
                "type": "rebalancing",
                "schedule": f"Daily at {hour:02d}:00",
                "enabled": True,
                "threshold": threshold_percent,
                "last_run": None
            }
            
            return {
                "status": "scheduled",
                "job_id": job_id,
                "schedule": f"Daily at {hour:02d}:00",
                "threshold": threshold_percent
            }
        else:
            if job_id in active_automations:
                del active_automations[job_id]
            
            return {
                "status": "disabled",
                "job_id": job_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/memory-optimization")
async def schedule_memory_optimization(
    day_of_week: int = 0,  # 0 = Monday, 6 = Sunday
    hour: int = 3,
    enabled: bool = True
) -> Dict[str, Any]:
    """
    Schedule weekly memory optimization
    """
    job_id = "memory_optimization"
    
    try:
        # Remove existing job if any
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        if enabled:
            # Schedule the job
            scheduler.add_job(
                _optimize_memories,
                CronTrigger(day_of_week=day_of_week, hour=hour, minute=0),
                id=job_id,
                name="Weekly Memory Optimization",
                replace_existing=True
            )
            
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            active_automations[job_id] = {
                "type": "memory_optimization",
                "schedule": f"Weekly on {days[day_of_week]} at {hour:02d}:00",
                "enabled": True,
                "last_run": None
            }
            
            return {
                "status": "scheduled",
                "job_id": job_id,
                "schedule": f"Weekly on {days[day_of_week]} at {hour:02d}:00"
            }
        else:
            if job_id in active_automations:
                del active_automations[job_id]
            
            return {
                "status": "disabled",
                "job_id": job_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automations")
async def get_active_automations() -> Dict[str, Any]:
    """
    Get all active automations
    """
    jobs = []
    
    for job in scheduler.get_jobs():
        job_info = {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        }
        
        # Add extra info from active_automations
        if job.id in active_automations:
            job_info.update(active_automations[job.id])
        
        jobs.append(job_info)
    
    return {
        "automations": jobs,
        "total": len(jobs)
    }


@router.post("/trigger/{job_id}")
async def trigger_automation(job_id: str) -> Dict[str, Any]:
    """
    Manually trigger an automation
    """
    try:
        job = scheduler.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Automation not found")
        
        # Run the job immediately
        job.func(*job.args, **job.kwargs)
        
        # Update last run
        if job_id in active_automations:
            active_automations[job_id]["last_run"] = datetime.now().isoformat()
        
        return {
            "status": "triggered",
            "job_id": job_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/automation/{job_id}")
async def delete_automation(job_id: str) -> Dict[str, Any]:
    """
    Delete an automation
    """
    try:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        if job_id in active_automations:
            del active_automations[job_id]
        
        return {
            "status": "deleted",
            "job_id": job_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Automation task functions

async def _check_treasury_health():
    """Daily treasury health check task"""
    
    try:
        # Get treasury metrics
        metrics = await treasury_monitor.get_dashboard_metrics()
        
        # Check alerts
        await treasury_monitor.check_alerts()
        
        # Log health status
        health_status = metrics['health']['status']
        
        # If critical, make conservative decision
        if health_status == 'CRITICAL':
            context = DecisionContext(
                current_treasury=metrics['current_balance'],
                market_condition='any',
                available_protocols=[],
                gas_price=50.0,  # High gas to discourage action
                risk_tolerance=0.1
            )
            
            await agent.decide(context)
        
        # Update last run
        if "daily_treasury_check" in active_automations:
            active_automations["daily_treasury_check"]["last_run"] = datetime.now().isoformat()
            
    except Exception as e:
        print(f"Treasury health check error: {e}")


async def _scan_market_opportunities():
    """Scan for market opportunities task"""
    
    try:
        # Get current treasury state
        treasury_state = await treasury_monitor.get_dashboard_metrics()
        
        # Only scan if healthy
        if treasury_state['health']['status'] != 'CRITICAL':
            # Get market opportunities
            opportunities = await agent.get_yield_opportunities()
            
            # Evaluate if any are worth pursuing
            if opportunities and treasury_state['current_balance'] > 500:
                context = DecisionContext(
                    current_treasury=treasury_state['current_balance'],
                    market_condition='opportunity_found',
                    available_protocols=[o['protocol'] for o in opportunities['opportunities']],
                    gas_price=15.0,
                    risk_tolerance=0.5
                )
                
                await agent.decide(context)
        
        # Update last run
        if "market_scan" in active_automations:
            active_automations["market_scan"]["last_run"] = datetime.now().isoformat()
            
    except Exception as e:
        print(f"Market scan error: {e}")


async def _check_rebalancing(threshold_percent: float):
    """Check if portfolio needs rebalancing"""
    
    try:
        # Get current positions
        # This would integrate with real portfolio data
        # For now, just log
        print(f"Checking rebalancing with {threshold_percent}% threshold")
        
        # Update last run
        if "daily_rebalancing" in active_automations:
            active_automations["daily_rebalancing"]["last_run"] = datetime.now().isoformat()
            
    except Exception as e:
        print(f"Rebalancing check error: {e}")


async def _optimize_memories():
    """Optimize memory storage task"""
    
    try:
        # Run memory optimization
        results = await memory_aggregator.optimize_memories()
        
        print(f"Memory optimization results: {results}")
        
        # Update last run
        if "memory_optimization" in active_automations:
            active_automations["memory_optimization"]["last_run"] = datetime.now().isoformat()
            
    except Exception as e:
        print(f"Memory optimization error: {e}")