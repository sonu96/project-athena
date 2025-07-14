"""
BigQuery client for Project Athena analytics
Handles data insertion and querying for memory analytics
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import json
import os
import asyncio
from contextlib import asynccontextmanager


class BigQueryClient:
    """
    Client for managing BigQuery operations
    """
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "project-athena-personal")
        self.dataset_id = os.getenv("BIGQUERY_DATASET", "athena_analytics")
        self.client = bigquery.Client(project=self.project_id)
        self.dataset_ref = f"{self.project_id}.{self.dataset_id}"
        
        # Table references
        self.tables = {
            "decisions": f"{self.dataset_ref}.agent_decisions",
            "treasury": f"{self.dataset_ref}.treasury_metrics",
            "memory": f"{self.dataset_ref}.memory_performance",
            "costs": f"{self.dataset_ref}.cost_analytics",
            "market": f"{self.dataset_ref}.market_observations"
        }
    
    async def insert_decision(self, decision_data: Dict[str, Any]) -> bool:
        """Insert agent decision record"""
        
        row = {
            "decision_id": decision_data["decision_id"],
            "timestamp": datetime.now(),
            "action": decision_data["action"],
            "protocol": decision_data.get("protocol"),
            "amount": decision_data.get("amount"),
            "expected_yield": decision_data.get("expected_yield"),
            "risk_score": decision_data.get("risk_score"),
            "confidence": decision_data.get("confidence"),
            "treasury_before": decision_data.get("treasury_before"),
            "market_condition": decision_data.get("market_condition"),
            "reasoning": decision_data.get("reasoning"),
            "memory_id": decision_data.get("memory_id")
        }
        
        return await self._insert_rows(self.tables["decisions"], [row])
    
    async def update_decision_outcome(self, 
                                    decision_id: str, 
                                    outcome_data: Dict[str, Any]) -> bool:
        """Update decision with actual outcome"""
        
        query = f"""
        UPDATE `{self.tables["decisions"]}`
        SET actual_yield = @actual_yield,
            gas_used = @gas_used,
            treasury_after = @treasury_after,
            success = @success
        WHERE decision_id = @decision_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("decision_id", "STRING", decision_id),
                bigquery.ScalarQueryParameter("actual_yield", "NUMERIC", outcome_data.get("actual_yield")),
                bigquery.ScalarQueryParameter("gas_used", "NUMERIC", outcome_data.get("gas_used")),
                bigquery.ScalarQueryParameter("treasury_after", "NUMERIC", outcome_data.get("treasury_after")),
                bigquery.ScalarQueryParameter("success", "BOOLEAN", outcome_data.get("success", False))
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            return True
        except Exception as e:
            print(f"Error updating decision outcome: {e}")
            return False
    
    async def insert_treasury_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Insert treasury metrics snapshot"""
        
        row = {
            "timestamp": datetime.now(),
            "balance": metrics["balance"],
            "daily_burn_rate": metrics.get("daily_burn_rate"),
            "weekly_burn_rate": metrics.get("weekly_burn_rate"),
            "runway_days": metrics.get("runway_days"),
            "health_score": metrics.get("health_score"),
            "risk_level": metrics.get("risk_level"),
            "alert_count": metrics.get("alert_count", 0),
            "spending_breakdown": {
                "gas_fees": metrics.get("spending", {}).get("gas_fees", 0),
                "api_calls": metrics.get("spending", {}).get("api_calls", 0),
                "failed_transactions": metrics.get("spending", {}).get("failed_transactions", 0),
                "decisions": metrics.get("spending", {}).get("decisions", 0),
                "other": metrics.get("spending", {}).get("other", 0)
            }
        }
        
        return await self._insert_rows(self.tables["treasury"], [row])
    
    async def insert_memory_performance(self, performance_data: Dict[str, Any]) -> bool:
        """Insert memory system performance metrics"""
        
        row = {
            "timestamp": datetime.now(),
            "total_memories": performance_data["total_memories"],
            "memories_by_type": {
                "decisions": performance_data.get("by_type", {}).get("decisions", 0),
                "learnings": performance_data.get("by_type", {}).get("learnings", 0),
                "market": performance_data.get("by_type", {}).get("market", 0),
                "protocol": performance_data.get("by_type", {}).get("protocol", 0),
                "survival": performance_data.get("by_type", {}).get("survival", 0)
            },
            "success_rate": performance_data.get("success_rate"),
            "avg_confidence": performance_data.get("avg_confidence"),
            "memory_health_score": performance_data.get("health_score"),
            "cleanup_count": performance_data.get("cleanup_count", 0),
            "storage_used_mb": performance_data.get("storage_mb", 0)
        }
        
        return await self._insert_rows(self.tables["memory"], [row])
    
    async def insert_cost_analytics(self, cost_data: List[Dict[str, Any]]) -> bool:
        """Insert daily cost analytics"""
        
        rows = []
        for category_data in cost_data:
            rows.append({
                "date": datetime.now().date(),
                "category": category_data["category"],
                "amount": category_data["amount"],
                "transaction_count": category_data.get("count", 0),
                "avg_cost_per_transaction": category_data.get("avg_cost"),
                "subcategory_breakdown": json.dumps(category_data.get("breakdown", {})),
                "optimization_applied": category_data.get("optimized", False)
            })
        
        return await self._insert_rows(self.tables["costs"], rows)
    
    async def insert_market_observation(self, market_data: Dict[str, Any]) -> bool:
        """Insert market observation data"""
        
        protocol_yields = []
        for protocol in market_data.get("protocols", []):
            protocol_yields.append({
                "protocol_name": protocol["name"],
                "apy": protocol.get("apy"),
                "tvl": protocol.get("tvl"),
                "risk_score": protocol.get("risk_score")
            })
        
        row = {
            "timestamp": datetime.now(),
            "market_condition": market_data["condition"],
            "protocol_yields": protocol_yields,
            "gas_price": market_data.get("gas_price"),
            "volatility_index": market_data.get("volatility"),
            "opportunities_found": market_data.get("opportunities_count", 0)
        }
        
        return await self._insert_rows(self.tables["market"], [row])
    
    async def get_recent_decisions(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent decisions for analysis"""
        
        query = f"""
        SELECT *
        FROM `{self.tables["decisions"]}`
        WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY timestamp DESC
        LIMIT 100
        """
        
        return await self._execute_query(query)
    
    async def get_strategy_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get strategy performance metrics"""
        
        query = f"""
        SELECT 
            action,
            protocol,
            COUNT(*) as decision_count,
            AVG(actual_yield) as avg_yield,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*) as success_rate,
            AVG(confidence) as avg_confidence
        FROM `{self.tables["decisions"]}`
        WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
            AND actual_yield IS NOT NULL
        GROUP BY action, protocol
        HAVING decision_count >= 3
        ORDER BY success_rate DESC, avg_yield DESC
        """
        
        return await self._execute_query(query)
    
    async def get_cost_breakdown(self, days: int = 7) -> Dict[str, float]:
        """Get cost breakdown by category"""
        
        query = f"""
        SELECT 
            category,
            SUM(amount) as total_cost
        FROM `{self.tables["costs"]}`
        WHERE date > DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        GROUP BY category
        ORDER BY total_cost DESC
        """
        
        results = await self._execute_query(query)
        return {row["category"]: row["total_cost"] for row in results}
    
    async def get_treasury_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get treasury balance trend"""
        
        query = f"""
        SELECT 
            DATE(timestamp) as date,
            AVG(balance) as avg_balance,
            MIN(balance) as min_balance,
            MAX(balance) as max_balance,
            AVG(runway_days) as avg_runway
        FROM `{self.tables["treasury"]}`
        WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY date
        ORDER BY date DESC
        """
        
        return await self._execute_query(query)
    
    # Helper methods
    
    async def _insert_rows(self, table_id: str, rows: List[Dict[str, Any]]) -> bool:
        """Insert rows into BigQuery table"""
        
        try:
            # Add inserted_at timestamp
            for row in rows:
                if "inserted_at" not in row:
                    row["inserted_at"] = datetime.now()
            
            errors = self.client.insert_rows_json(table_id, rows)
            
            if errors:
                print(f"Error inserting rows into {table_id}: {errors}")
                return False
            
            return True
        except Exception as e:
            print(f"Exception inserting rows: {e}")
            return False
    
    async def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error executing query: {e}")
            return []
    
    async def batch_insert_hourly_data(self, batch_data: Dict[str, Any]) -> Dict[str, bool]:
        """Batch insert hourly aggregated data"""
        
        results = {}
        
        # Insert treasury metrics
        if "treasury" in batch_data:
            results["treasury"] = await self.insert_treasury_metrics(batch_data["treasury"])
        
        # Insert memory performance
        if "memory" in batch_data:
            results["memory"] = await self.insert_memory_performance(batch_data["memory"])
        
        # Insert recent decisions
        if "decisions" in batch_data:
            for decision in batch_data["decisions"]:
                await self.insert_decision(decision)
            results["decisions"] = True
        
        return results
    
    async def cleanup_old_data(self) -> Dict[str, int]:
        """Clean up old data based on retention policy"""
        
        cleanup_results = {}
        
        # Define retention policies (in days)
        retention_policies = {
            "treasury_metrics": 90,
            "memory_performance": 90,
            "market_observations": 30
        }
        
        for table, days in retention_policies.items():
            if table in ["treasury_metrics", "memory_performance", "market_observations"]:
                query = f"""
                DELETE FROM `{self.tables[table.split('_')[0]]}`
                WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
                """
                
                try:
                    query_job = self.client.query(query)
                    query_job.result()
                    cleanup_results[table] = query_job.num_dml_affected_rows
                except Exception as e:
                    print(f"Error cleaning up {table}: {e}")
                    cleanup_results[table] = 0
        
        return cleanup_results