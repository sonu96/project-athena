"""
BigQuery Client for analytics and historical data

Handles long-term storage and analysis of agent performance.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from ..config import settings

logger = logging.getLogger(__name__)


class BigQueryClient:
    """
    Client for Google BigQuery operations
    
    Tables:
    - agent_metrics: Performance metrics
    - pool_observations: Historical pool data
    - memory_usage: Memory effectiveness tracking
    - decision_log: All decisions made
    """
    
    def __init__(self):
        try:
            self.client = bigquery.Client(project=settings.gcp_project_id)
            self.dataset_id = settings.bigquery_dataset
            self.dataset_ref = self.client.dataset(self.dataset_id)
            self._initialized = True
            logger.info("✅ BigQuery client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery: {e}")
            self._initialized = False
            self.client = None
    
    async def ensure_dataset_exists(self) -> bool:
        """Ensure the dataset exists"""
        if not self._initialized:
            return False
        
        try:
            # Check if dataset exists
            self.client.get_dataset(self.dataset_ref)
            return True
        except:
            try:
                # Create dataset
                dataset = bigquery.Dataset(self.dataset_ref)
                dataset.location = "US"
                self.client.create_dataset(dataset)
                logger.info(f"Created BigQuery dataset: {self.dataset_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to create dataset: {e}")
                return False
    
    async def ensure_tables_exist(self) -> bool:
        """Ensure all required tables exist"""
        if not self._initialized:
            return False
        
        tables = {
            "agent_metrics": [
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("agent_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("cycle_count", "INTEGER"),
                bigquery.SchemaField("treasury_balance", "FLOAT"),
                bigquery.SchemaField("emotional_state", "STRING"),
                bigquery.SchemaField("emotional_intensity", "FLOAT"),
                bigquery.SchemaField("memories_formed", "INTEGER"),
                bigquery.SchemaField("patterns_active", "INTEGER"),
                bigquery.SchemaField("total_cost", "FLOAT"),
                bigquery.SchemaField("llm_cost", "FLOAT"),
                bigquery.SchemaField("days_until_bankruptcy", "FLOAT"),
            ],
            "pool_observations": [
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("agent_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("pool_address", "STRING"),
                bigquery.SchemaField("pool_type", "STRING"),
                bigquery.SchemaField("token0_symbol", "STRING"),
                bigquery.SchemaField("token1_symbol", "STRING"),
                bigquery.SchemaField("tvl_usd", "FLOAT"),
                bigquery.SchemaField("volume_24h_usd", "FLOAT"),
                bigquery.SchemaField("fee_apy", "FLOAT"),
                bigquery.SchemaField("reward_apy", "FLOAT"),
                bigquery.SchemaField("total_apy", "FLOAT"),
            ],
            "memory_usage": [
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("memory_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("category", "STRING"),
                bigquery.SchemaField("usage_count", "INTEGER"),
                bigquery.SchemaField("influenced_decisions", "INTEGER"),
                bigquery.SchemaField("importance_score", "FLOAT"),
            ],
            "decision_log": [
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("agent_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("decision_type", "STRING"),
                bigquery.SchemaField("rationale", "STRING"),
                bigquery.SchemaField("confidence", "FLOAT"),
                bigquery.SchemaField("cost", "FLOAT"),
                bigquery.SchemaField("outcome", "STRING"),
            ]
        }
        
        for table_name, schema in tables.items():
            try:
                table_id = f"{settings.gcp_project_id}.{self.dataset_id}.{table_name}"
                table = bigquery.Table(table_id, schema=schema)
                self.client.create_table(table)
                logger.info(f"Created table: {table_name}")
            except Exception as e:
                if "Already Exists" in str(e):
                    logger.debug(f"Table {table_name} already exists")
                else:
                    logger.error(f"Failed to create table {table_name}: {e}")
                    return False
        
        return True
    
    async def insert_rows(
        self,
        table_name: str,
        rows: List[Dict[str, Any]]
    ) -> bool:
        """
        Insert rows into a table
        
        Args:
            table_name: Table name
            rows: List of row data
            
        Returns:
            Success status
        """
        if not self._initialized or not rows:
            return False
        
        try:
            table_id = f"{settings.gcp_project_id}.{self.dataset_id}.{table_name}"
            table = self.client.get_table(table_id)
            
            errors = self.client.insert_rows_json(table, rows)
            
            if errors:
                logger.error(f"Failed to insert rows: {errors}")
                return False
            
            logger.debug(f"Inserted {len(rows)} rows into {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert rows: {e}")
            return False
    
    async def query(
        self,
        query_string: str,
        parameters: Optional[List[bigquery.ScalarQueryParameter]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query
        
        Args:
            query_string: SQL query
            parameters: Query parameters
            
        Returns:
            Query results
        """
        if not self._initialized:
            return []
        
        try:
            job_config = bigquery.QueryJobConfig()
            if parameters:
                job_config.query_parameters = parameters
            
            query_job = self.client.query(query_string, job_config=job_config)
            results = query_job.result()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    # Agent-specific methods
    
    async def log_agent_metrics(
        self,
        agent_id: str,
        metrics: Dict[str, Any]
    ) -> bool:
        """Log agent performance metrics"""
        row = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            **metrics
        }
        return await self.insert_rows("agent_metrics", [row])
    
    async def log_pool_observation(
        self,
        agent_id: str,
        pool_data: Dict[str, Any]
    ) -> bool:
        """Log pool observation"""
        row = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            **pool_data
        }
        return await self.insert_rows("pool_observations", [row])
    
    async def log_memory_usage(
        self,
        memory_data: Dict[str, Any]
    ) -> bool:
        """Log memory usage"""
        row = {
            "timestamp": datetime.utcnow().isoformat(),
            **memory_data
        }
        return await self.insert_rows("memory_usage", [row])
    
    async def log_decision(
        self,
        agent_id: str,
        decision: Dict[str, Any]
    ) -> bool:
        """Log decision"""
        row = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            **decision
        }
        return await self.insert_rows("decision_log", [row])
    
    async def get_agent_summary(
        self,
        agent_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get agent performance summary"""
        query = f"""
        SELECT
            COUNT(*) as total_cycles,
            AVG(treasury_balance) as avg_balance,
            MIN(treasury_balance) as min_balance,
            MAX(treasury_balance) as max_balance,
            SUM(total_cost) as total_spent,
            COUNT(DISTINCT emotional_state) as emotional_states_experienced
        FROM `{settings.gcp_project_id}.{self.dataset_id}.agent_metrics`
        WHERE agent_id = @agent_id
            AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
        """
        
        parameters = [
            bigquery.ScalarQueryParameter("agent_id", "STRING", agent_id),
            bigquery.ScalarQueryParameter("days", "INT64", days)
        ]
        
        results = await self.query(query, parameters)
        return results[0] if results else {}