"""
Cost Guardian - Monitors and enforces the $30 budget limit
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
from google.cloud import bigquery
from google.cloud import firestore

from ..config.gcp_config import gcp_config
from ..data.firestore_client import FirestoreClient
from ..data.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class CostGuardian:
    """Monitors costs and enforces budget limits"""
    
    def __init__(self, firestore_client: FirestoreClient, bigquery_client: BigQueryClient):
        self.firestore = firestore_client
        self.bigquery = bigquery_client
        self.bq_client = gcp_config.bigquery_client
        
        # Budget configuration
        self.TOTAL_BUDGET = 30.0  # $30 hard limit
        self.SHUTDOWN_THRESHOLD = 0.90  # Shutdown at 90% ($27)
        self.WARNING_THRESHOLD = 0.75   # Warning at 75% ($22.50)
        self.CAUTION_THRESHOLD = 0.50   # Caution at 50% ($15)
        
        # Cost tracking
        self.current_month_spend = 0.0
        self.daily_spend = 0.0
        self.emergency_mode = False
        
        logger.info("💂 Cost Guardian initialized - $30 budget protection active")
    
    async def check_budget_status(self) -> Dict[str, Any]:
        """Check current budget status and spending"""
        try:
            # Get current month spending from BigQuery
            query = """
            SELECT 
                SUM(cost_usd) as total_cost,
                COUNT(*) as transaction_count,
                MAX(timestamp) as last_transaction
            FROM `{}.{}.cost_tracking`
            WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """.format(gcp_config.project_id, gcp_config.bigquery_dataset)
            
            query_job = self.bq_client.query(query)
            results = list(query_job.result())
            
            if results and results[0].total_cost:
                self.current_month_spend = float(results[0].total_cost)
            else:
                self.current_month_spend = 0.0
            
            # Calculate budget status
            budget_used_percent = (self.current_month_spend / self.TOTAL_BUDGET) * 100
            budget_remaining = self.TOTAL_BUDGET - self.current_month_spend
            
            # Determine status level
            if budget_used_percent >= self.SHUTDOWN_THRESHOLD * 100:
                status = "CRITICAL"
                self.emergency_mode = True
            elif budget_used_percent >= self.WARNING_THRESHOLD * 100:
                status = "WARNING"
            elif budget_used_percent >= self.CAUTION_THRESHOLD * 100:
                status = "CAUTION"
            else:
                status = "HEALTHY"
            
            # Calculate burn rate
            days_in_month = 30
            days_elapsed = datetime.now().day
            daily_burn_rate = self.current_month_spend / days_elapsed if days_elapsed > 0 else 0
            projected_month_spend = daily_burn_rate * days_in_month
            days_until_limit = (budget_remaining / daily_burn_rate) if daily_burn_rate > 0 else 999
            
            budget_status = {
                "status": status,
                "budget_limit": self.TOTAL_BUDGET,
                "current_spend": round(self.current_month_spend, 2),
                "budget_remaining": round(budget_remaining, 2),
                "budget_used_percent": round(budget_used_percent, 1),
                "daily_burn_rate": round(daily_burn_rate, 2),
                "projected_month_spend": round(projected_month_spend, 2),
                "days_until_limit": round(days_until_limit, 1),
                "emergency_mode": self.emergency_mode,
                "timestamp": datetime.utcnow()
            }
            
            # Log status
            if status == "CRITICAL":
                logger.critical(f"🚨 BUDGET CRITICAL: ${self.current_month_spend:.2f} / ${self.TOTAL_BUDGET} ({budget_used_percent:.1f}%)")
            elif status == "WARNING":
                logger.warning(f"⚠️ BUDGET WARNING: ${self.current_month_spend:.2f} / ${self.TOTAL_BUDGET} ({budget_used_percent:.1f}%)")
            else:
                logger.info(f"💰 Budget: ${self.current_month_spend:.2f} / ${self.TOTAL_BUDGET} ({budget_used_percent:.1f}%)")
            
            # Store status in Firestore
            self.firestore.db.collection('budget_status').document('current').set(budget_status)
            
            return budget_status
            
        except Exception as e:
            logger.error(f"❌ Error checking budget: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "emergency_mode": True  # Fail safe
            }
    
    async def record_cost(self, service: str, operation: str, cost_usd: float, metadata: Dict = None) -> bool:
        """Record a cost transaction"""
        try:
            # Check if we should allow this transaction
            if self.emergency_mode and cost_usd > 0.01:
                logger.error(f"❌ BLOCKED: Emergency mode active, rejecting ${cost_usd:.4f} transaction")
                return False
            
            # Record the cost
            cost_record = {
                "timestamp": datetime.utcnow(),
                "service": service,
                "operation": operation,
                "cost_usd": cost_usd,
                "metadata": metadata or {},
                "budget_remaining": self.TOTAL_BUDGET - self.current_month_spend - cost_usd
            }
            
            # Insert to BigQuery
            await self.bigquery.insert_cost_tracking([cost_record])
            
            # Update running total
            self.current_month_spend += cost_usd
            
            # Check if we've hit emergency threshold
            if self.current_month_spend >= (self.TOTAL_BUDGET * self.SHUTDOWN_THRESHOLD):
                await self.activate_emergency_shutdown()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recording cost: {e}")
            return False
    
    async def activate_emergency_shutdown(self):
        """Activate emergency shutdown to prevent overspending"""
        logger.critical("💀 EMERGENCY SHUTDOWN ACTIVATED - BUDGET LIMIT REACHED")
        
        self.emergency_mode = True
        
        # Set emergency flag in Firestore
        emergency_doc = {
            "active": True,
            "activated_at": datetime.utcnow(),
            "reason": "Budget limit reached",
            "current_spend": self.current_month_spend,
            "budget_limit": self.TOTAL_BUDGET
        }
        
        self.firestore.db.collection('system_state').document('emergency').set(emergency_doc)
        
        # Log to BigQuery
        await self.bigquery.insert_decision({
            "timestamp": datetime.utcnow(),
            "decision_type": "emergency_shutdown",
            "reasoning": f"Budget exceeded {self.SHUTDOWN_THRESHOLD*100}% threshold",
            "action_taken": "all_operations_suspended",
            "expected_outcome": "prevent_overspending",
            "cost_usd": 0,
            "success": True
        })
    
    async def get_cost_breakdown(self, days: int = 7) -> Dict[str, Any]:
        """Get detailed cost breakdown by service"""
        try:
            query = f"""
            SELECT 
                service,
                COUNT(*) as transaction_count,
                SUM(cost_usd) as total_cost,
                AVG(cost_usd) as avg_cost,
                MAX(cost_usd) as max_cost
            FROM `{gcp_config.project_id}.{gcp_config.bigquery_dataset}.cost_tracking`
            WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
            GROUP BY service
            ORDER BY total_cost DESC
            """
            
            query_job = self.bq_client.query(query)
            results = list(query_job.result())
            
            breakdown = {
                "period_days": days,
                "services": {},
                "total_cost": 0.0
            }
            
            for row in results:
                breakdown["services"][row.service] = {
                    "transactions": row.transaction_count,
                    "total_cost": round(float(row.total_cost), 4),
                    "avg_cost": round(float(row.avg_cost), 6),
                    "max_cost": round(float(row.max_cost), 4)
                }
                breakdown["total_cost"] += float(row.total_cost)
            
            breakdown["total_cost"] = round(breakdown["total_cost"], 2)
            
            return breakdown
            
        except Exception as e:
            logger.error(f"❌ Error getting cost breakdown: {e}")
            return {"error": str(e)}
    
    def can_afford_operation(self, estimated_cost: float) -> bool:
        """Check if we can afford an operation"""
        if self.emergency_mode:
            return False
        
        if self.current_month_spend + estimated_cost > (self.TOTAL_BUDGET * self.WARNING_THRESHOLD):
            logger.warning(f"⚠️ Operation cost ${estimated_cost:.4f} would exceed warning threshold")
            return False
        
        return True
    
    async def get_daily_budget_allowance(self) -> float:
        """Calculate safe daily spending allowance"""
        days_remaining = 30 - datetime.now().day
        budget_remaining = self.TOTAL_BUDGET - self.current_month_spend
        
        if days_remaining <= 0:
            return 0.0
        
        # Conservative daily allowance (80% of remaining / days)
        daily_allowance = (budget_remaining * 0.8) / days_remaining
        
        return max(0.0, min(daily_allowance, 2.0))  # Cap at $2/day


# Example usage
async def test_cost_guardian():
    """Test cost guardian"""
    try:
        from ..data.firestore_client import FirestoreClient
        from ..data.bigquery_client import BigQueryClient
        
        firestore = FirestoreClient()
        bigquery = BigQueryClient()
        
        await firestore.initialize_database()
        await bigquery.initialize_dataset()
        
        guardian = CostGuardian(firestore, bigquery)
        
        # Check budget
        status = await guardian.check_budget_status()
        logger.info(f"Budget Status: {status}")
        
        # Record a test cost
        await guardian.record_cost(
            service="gemini",
            operation="test_query",
            cost_usd=0.00001,
            metadata={"tokens": 100}
        )
        
        # Get breakdown
        breakdown = await guardian.get_cost_breakdown(7)
        logger.info(f"Cost Breakdown: {breakdown}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_cost_guardian())