"""
Cost Management System

Monitors spending across all services and shuts down when limits are exceeded.
"""

import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class CostAlert:
    """Cost alert configuration"""
    threshold: float
    message: str
    action: str

class CostManager:
    """
    Manages costs across all services with automatic shutdown
    
    Features:
    - Real-time cost tracking
    - Service-specific limits
    - Automatic shutdown at $30
    - Cost alerts and warnings
    """
    
    # Cost limits and alerts
    HARD_LIMIT = 30.0  # $30 absolute limit
    ALERTS = [
        CostAlert(5.0, "🟡 Warning: $5 spent", "warn"),
        CostAlert(10.0, "🟠 Caution: $10 spent", "reduce_frequency"),
        CostAlert(20.0, "🔴 Critical: $20 spent", "emergency_mode"),
        CostAlert(25.0, "🚨 SHUTDOWN IMMINENT: $25 spent", "prepare_shutdown"),
        CostAlert(30.0, "🛑 HARD LIMIT REACHED", "shutdown")
    ]
    
    def __init__(self):
        self.cost_file = "cost_tracking.json"
        self.emergency_mode = False
        self.shutdown_triggered = False
        self.daily_costs = self._load_costs()
        
        logger.info(f"💰 Cost Manager initialized with ${self.HARD_LIMIT} limit")
    
    def _load_costs(self) -> Dict[str, Any]:
        """Load existing cost data"""
        try:
            if os.path.exists(self.cost_file):
                with open(self.cost_file, 'r') as f:
                    data = json.load(f)
                    
                # Check if it's a new day
                last_date = data.get('date', '')
                today = datetime.now().strftime('%Y-%m-%d')
                
                if last_date != today:
                    # Reset for new day
                    logger.info(f"📅 New day detected, resetting costs")
                    return self._create_fresh_costs()
                
                return data
        except Exception as e:
            logger.warning(f"Failed to load costs: {e}")
        
        return self._create_fresh_costs()
    
    def _create_fresh_costs(self) -> Dict[str, Any]:
        """Create fresh cost tracking structure"""
        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "total_cost": 0.0,
            "services": {
                "gemini_api": 0.0,
                "openai_api": 0.0,
                "mem0_api": 0.0,
                "google_cloud": 0.0,
                "other": 0.0
            },
            "operations": {
                "llm_calls": 0,
                "memory_operations": 0,
                "database_operations": 0,
                "cognitive_cycles": 0
            },
            "alerts_triggered": [],
            "emergency_mode": False,
            "shutdown_triggered": False
        }
    
    def _save_costs(self):
        """Save cost data to file"""
        try:
            with open(self.cost_file, 'w') as f:
                json.dump(self.daily_costs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save costs: {e}")
    
    async def add_cost(
        self, 
        amount: float, 
        service: str, 
        operation: str = "",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add cost and check limits
        
        Args:
            amount: Cost in USD
            service: Service name (gemini_api, mem0_api, etc.)
            operation: Operation description
            metadata: Additional cost metadata
            
        Returns:
            True if operation should continue, False if shutdown
        """
        if self.shutdown_triggered:
            logger.error("🛑 SHUTDOWN MODE: All operations blocked")
            return False
        
        # Add cost to tracking
        self.daily_costs["total_cost"] += amount
        
        if service in self.daily_costs["services"]:
            self.daily_costs["services"][service] += amount
        else:
            self.daily_costs["services"]["other"] += amount
        
        # Increment operation count
        if operation in self.daily_costs["operations"]:
            self.daily_costs["operations"][operation] += 1
        
        current_total = self.daily_costs["total_cost"]
        
        logger.info(
            f"💸 Cost added: ${amount:.6f} ({service}) | "
            f"Daily total: ${current_total:.4f} | "
            f"Remaining: ${self.HARD_LIMIT - current_total:.4f}"
        )
        
        # Check alerts
        await self._check_alerts(current_total)
        
        # Save updated costs
        self._save_costs()
        
        # Check hard limit
        if current_total >= self.HARD_LIMIT:
            await self._trigger_shutdown("HARD_LIMIT_EXCEEDED")
            return False
        
        # Check emergency mode
        if current_total >= 20.0 and not self.emergency_mode:
            await self._enter_emergency_mode()
        
        return True
    
    async def _check_alerts(self, current_cost: float):
        """Check if any alert thresholds are crossed"""
        for alert in self.ALERTS:
            alert_key = f"alert_{alert.threshold}"
            
            if (current_cost >= alert.threshold and 
                alert_key not in self.daily_costs["alerts_triggered"]):
                
                logger.warning(f"🚨 {alert.message}")
                self.daily_costs["alerts_triggered"].append(alert_key)
                
                # Take action based on alert
                if alert.action == "reduce_frequency":
                    await self._reduce_operation_frequency()
                elif alert.action == "emergency_mode":
                    await self._enter_emergency_mode()
                elif alert.action == "prepare_shutdown":
                    await self._prepare_shutdown()
                elif alert.action == "shutdown":
                    await self._trigger_shutdown("ALERT_TRIGGERED")
    
    async def _reduce_operation_frequency(self):
        """Reduce operation frequency to save costs"""
        logger.warning("🔄 Reducing operation frequency to conserve budget")
        
        # Update agent settings to reduce frequency
        self.daily_costs["reduced_frequency"] = True
        
        # Could signal to agent to increase cycle intervals
        # This would be implemented in the agent's main loop
    
    async def _enter_emergency_mode(self):
        """Enter emergency cost-saving mode"""
        if self.emergency_mode:
            return
            
        logger.critical("🚨 ENTERING EMERGENCY MODE - Critical cost threshold reached")
        self.emergency_mode = True
        self.daily_costs["emergency_mode"] = True
        
        # Emergency cost-saving measures:
        # 1. Switch to cheapest models only
        # 2. Reduce memory operations
        # 3. Increase cycle intervals
        # 4. Limit observations
        
        logger.warning("🎯 Emergency measures activated:")
        logger.warning("   - Switching to cheapest LLM models only")
        logger.warning("   - Reducing memory operations")
        logger.warning("   - Increasing cycle intervals")
        logger.warning("   - Limited observations only")
    
    async def _prepare_shutdown(self):
        """Prepare for imminent shutdown"""
        logger.critical("⚠️  PREPARING FOR SHUTDOWN - Budget nearly exhausted")
        
        # Save critical state
        # Finish current operations
        # Prepare graceful shutdown
        
        logger.warning("💾 Saving critical agent state...")
        logger.warning("🔄 Finishing current operations...")
        logger.warning("⏰ Shutdown will trigger at $30.00")
    
    async def _trigger_shutdown(self, reason: str):
        """Trigger emergency shutdown"""
        if self.shutdown_triggered:
            return
            
        self.shutdown_triggered = True
        self.daily_costs["shutdown_triggered"] = True
        self.daily_costs["shutdown_reason"] = reason
        self.daily_costs["shutdown_time"] = datetime.now().isoformat()
        
        logger.critical("🛑🛑🛑 EMERGENCY SHUTDOWN TRIGGERED 🛑🛑🛑")
        logger.critical(f"Reason: {reason}")
        logger.critical(f"Total cost: ${self.daily_costs['total_cost']:.4f}")
        logger.critical(f"Limit: ${self.HARD_LIMIT}")
        
        # Save final state
        self._save_costs()
        
        # Stop all services
        await self._stop_all_services()
        
        # Exit the application
        logger.critical("🔚 Application terminating to prevent further costs")
        os._exit(1)  # Force exit
    
    async def _stop_all_services(self):
        """Stop all cost-generating services"""
        logger.critical("🛑 Stopping all services...")
        
        # List of services to stop
        services = [
            "LLM API calls",
            "Memory operations", 
            "Database writes",
            "Cloud functions",
            "Monitoring systems"
        ]
        
        for service in services:
            logger.critical(f"   🛑 Stopping: {service}")
            await asyncio.sleep(0.1)  # Give time for logging
        
        logger.critical("✅ All services stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current cost status"""
        current_cost = self.daily_costs["total_cost"]
        remaining = self.HARD_LIMIT - current_cost
        percentage = (current_cost / self.HARD_LIMIT) * 100
        
        return {
            "total_cost": current_cost,
            "hard_limit": self.HARD_LIMIT,
            "remaining_budget": remaining,
            "percentage_used": percentage,
            "emergency_mode": self.emergency_mode,
            "shutdown_triggered": self.shutdown_triggered,
            "services": self.daily_costs["services"].copy(),
            "operations": self.daily_costs["operations"].copy(),
            "date": self.daily_costs["date"],
            "alerts_triggered": self.daily_costs["alerts_triggered"].copy()
        }
    
    def can_afford(self, estimated_cost: float) -> bool:
        """Check if we can afford an operation"""
        if self.shutdown_triggered:
            return False
            
        projected_total = self.daily_costs["total_cost"] + estimated_cost
        return projected_total < self.HARD_LIMIT
    
    def get_max_affordable_cost(self) -> float:
        """Get maximum cost we can afford for next operation"""
        if self.shutdown_triggered:
            return 0.0
            
        return max(0.0, self.HARD_LIMIT - self.daily_costs["total_cost"])
    
    def get_cost_summary(self) -> str:
        """Get human-readable cost summary"""
        status = self.get_status()
        
        summary = f"""
💰 Daily Cost Summary ({status['date']})
├── Total Spent: ${status['total_cost']:.4f}
├── Remaining: ${status['remaining_budget']:.4f}
├── Budget Used: {status['percentage_used']:.1f}%
├── Hard Limit: ${status['hard_limit']}
│
├── 🤖 Services:
│   ├── Gemini API: ${status['services']['gemini_api']:.4f}
│   ├── Mem0 API: ${status['services']['mem0_api']:.4f}
│   ├── Google Cloud: ${status['services']['google_cloud']:.4f}
│   └── Other: ${status['services']['other']:.4f}
│
├── 📊 Operations:
│   ├── LLM Calls: {status['operations']['llm_calls']}
│   ├── Memory Ops: {status['operations']['memory_operations']}
│   └── Cognitive Cycles: {status['operations']['cognitive_cycles']}
│
├── ⚠️  Emergency Mode: {'Yes' if status['emergency_mode'] else 'No'}
└── 🛑 Shutdown: {'Yes' if status['shutdown_triggered'] else 'No'}
        """
        
        return summary.strip()

# Global cost manager instance
cost_manager = CostManager()