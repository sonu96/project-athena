"""
BigQuery client for analytics and historical data storage
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import logging

from ..config.gcp_config import gcp_config
from ..config.settings import settings

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Client for interacting with BigQuery for analytics"""
    
    def __init__(self):
        self.client = gcp_config.bigquery_client
        self.dataset_id = settings.bigquery_dataset
        self.project_id = settings.gcp_project_id
        
        # Table configurations - Updated for yield optimization
        self.tables = {
            # Core tables
            'market_data': 'market_data',
            'treasury_snapshots': 'treasury_snapshots',
            'decisions': 'agent_decisions',
            'costs': 'cost_tracking',
            
            # Yield optimization tables
            'yield_performance': 'yield_performance',
            'rebalancing_events': 'rebalancing_events',
            'compound_events': 'compound_events',
            'risk_events': 'risk_events',
            'gas_patterns': 'gas_patterns',
            'bridge_performance': 'bridge_performance',
            
            # Enhanced tables
            'memory_effectiveness': 'memory_effectiveness',
            'protocol_analytics': 'protocol_analytics'
        }
    
    async def initialize_dataset(self) -> bool:
        """Initialize BigQuery dataset and tables"""
        try:
            # Create dataset if it doesn't exist
            dataset_id = f"{self.project_id}.{self.dataset_id}"
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = "US"
            dataset.description = "Athena DeFi Agent analytics data"
            
            try:
                dataset = self.client.create_dataset(dataset, exists_ok=True)
                logger.info(f"✅ Dataset {dataset_id} is ready")
            except GoogleCloudError as e:
                if "already exists" not in str(e):
                    raise e
            
            # Create tables
            await self._create_tables()
            
            return True
        except Exception as e:
            logger.error(f"❌ Error initializing BigQuery: {e}")
            return False
    
    async def _create_tables(self):
        """Create all required tables with schemas"""
        
        # Market Data Table
        market_data_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("btc_price", "FLOAT64"),
            bigquery.SchemaField("eth_price", "FLOAT64"),
            bigquery.SchemaField("btc_24h_change", "FLOAT64"),
            bigquery.SchemaField("eth_24h_change", "FLOAT64"),
            bigquery.SchemaField("total_market_cap", "FLOAT64"),
            bigquery.SchemaField("defi_tvl", "FLOAT64"),
            bigquery.SchemaField("fear_greed_index", "INTEGER"),
            bigquery.SchemaField("gas_price_gwei", "FLOAT64"),
            bigquery.SchemaField("data_source", "STRING"),
            bigquery.SchemaField("data_quality_score", "FLOAT64"),
        ]
        await self._create_table('market_data', market_data_schema, 
                               clustering_fields=["data_source"],
                               time_partitioning_field="timestamp")
        
        # Treasury Snapshots Table
        treasury_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("balance_usd", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("daily_burn_rate", "FLOAT64"),
            bigquery.SchemaField("days_until_bankruptcy", "INTEGER"),
            bigquery.SchemaField("emotional_state", "STRING"),
            bigquery.SchemaField("risk_tolerance", "FLOAT64"),
            bigquery.SchemaField("confidence_level", "FLOAT64"),
            bigquery.SchemaField("snapshot_type", "STRING"),  # hourly, daily, event-driven
        ]
        await self._create_table('treasury_snapshots', treasury_schema,
                               clustering_fields=["emotional_state"],
                               time_partitioning_field="timestamp")
        
        # Agent Decisions Table
        decisions_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("decision_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("decision_type", "STRING"),
            bigquery.SchemaField("market_condition", "STRING"),
            bigquery.SchemaField("treasury_state", "STRING"),
            bigquery.SchemaField("confidence_score", "FLOAT64"),
            bigquery.SchemaField("reasoning", "STRING"),
            bigquery.SchemaField("memory_context", "JSON"),
            bigquery.SchemaField("outcome", "STRING"),
            bigquery.SchemaField("cost_usd", "FLOAT64"),
        ]
        await self._create_table('agent_decisions', decisions_schema,
                               time_partitioning_field="timestamp")
        
        # Cost Tracking Table
        costs_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("cost_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("amount_usd", "FLOAT64", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("operation", "STRING"),
            bigquery.SchemaField("llm_tokens", "INTEGER"),
            bigquery.SchemaField("api_calls", "INTEGER"),
        ]
        await self._create_table('cost_tracking', costs_schema,
                               clustering_fields=["cost_type"],
                               time_partitioning_field="timestamp")
        
        # Memory Formations Table
        memories_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("memory_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("importance", "FLOAT64"),
            bigquery.SchemaField("content", "STRING"),
            bigquery.SchemaField("metadata", "JSON"),
            bigquery.SchemaField("formation_trigger", "STRING"),
            bigquery.SchemaField("recall_count", "INTEGER"),
        ]
        await self._create_table('memory_formations', memories_schema,
                               clustering_fields=["category"],
                               time_partitioning_field="timestamp")
        
        # Performance Metrics Table
        performance_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("metric_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("value", "FLOAT64"),
            bigquery.SchemaField("unit", "STRING"),
            bigquery.SchemaField("context", "JSON"),
        ]
        await self._create_table('performance_metrics', performance_schema,
                               clustering_fields=["metric_type"],
                               time_partitioning_field="timestamp")
    
    async def _create_table(self, table_name: str, schema: List[bigquery.SchemaField], 
                          clustering_fields: Optional[List[str]] = None,
                          time_partitioning_field: Optional[str] = None):
        """Create a single table with the specified schema"""
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)
        
        # Add time partitioning if specified
        if time_partitioning_field:
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field=time_partitioning_field
            )
        
        # Add clustering if specified
        if clustering_fields:
            table.clustering_fields = clustering_fields
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            logger.info(f"✅ Table {table_name} is ready")
        except Exception as e:
            logger.error(f"❌ Error creating table {table_name}: {e}")
    
    async def insert_market_data(self, market_data: Dict[str, Any]) -> bool:
        """Insert market data for analysis"""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{self.tables['market_data']}"
            table = self.client.get_table(table_id)
            
            # Ensure timestamp
            if 'timestamp' not in market_data:
                market_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            errors = self.client.insert_rows_json(table, [market_data])
            if errors:
                logger.error(f"❌ BigQuery insert errors: {errors}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"❌ Error inserting market data: {e}")
            return False
    
    async def insert_treasury_snapshot(self, treasury_data: Dict[str, Any]) -> bool:
        """Insert treasury snapshot"""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{self.tables['treasury_snapshots']}"
            table = self.client.get_table(table_id)
            
            if 'timestamp' not in treasury_data:
                treasury_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            errors = self.client.insert_rows_json(table, [treasury_data])
            return len(errors) == 0
        except Exception as e:
            logger.error(f"❌ Error inserting treasury snapshot: {e}")
            return False
    
    async def insert_decision(self, decision_data: Dict[str, Any]) -> bool:
        """Insert agent decision record"""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{self.tables['decisions']}"
            table = self.client.get_table(table_id)
            
            if 'timestamp' not in decision_data:
                decision_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            errors = self.client.insert_rows_json(table, [decision_data])
            return len(errors) == 0
        except Exception as e:
            logger.error(f"❌ Error inserting decision: {e}")
            return False
    
    async def get_market_patterns(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get market patterns for agent learning"""
        query = f"""
        SELECT 
            DATE(timestamp) as date,
            AVG(btc_price) as avg_btc_price,
            AVG(eth_price) as avg_eth_price,
            STDDEV(btc_price) as btc_volatility,
            STDDEV(eth_price) as eth_volatility,
            AVG(fear_greed_index) as avg_sentiment,
            COUNT(*) as data_points
        FROM `{self.project_id}.{self.dataset_id}.{self.tables['market_data']}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY date
        ORDER BY date DESC
        """
        
        try:
            results = self.client.query(query).result()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Error getting market patterns: {e}")
            return []
    
    async def get_cost_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get detailed cost analytics"""
        query = f"""
        SELECT 
            DATE(timestamp) as date,
            cost_type,
            SUM(amount_usd) as total_cost,
            COUNT(*) as operation_count,
            AVG(amount_usd) as avg_cost_per_operation
        FROM `{self.project_id}.{self.dataset_id}.{self.tables['costs']}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY date, cost_type
        ORDER BY date DESC, total_cost DESC
        """
        
        try:
            results = self.client.query(query).result()
            
            analytics = {
                'daily_breakdown': {},
                'type_breakdown': {},
                'total_cost': 0,
                'total_operations': 0
            }
            
            for row in results:
                date_str = row['date'].strftime('%Y-%m-%d')
                
                if date_str not in analytics['daily_breakdown']:
                    analytics['daily_breakdown'][date_str] = {}
                
                analytics['daily_breakdown'][date_str][row['cost_type']] = {
                    'total': row['total_cost'],
                    'count': row['operation_count'],
                    'average': row['avg_cost_per_operation']
                }
                
                if row['cost_type'] not in analytics['type_breakdown']:
                    analytics['type_breakdown'][row['cost_type']] = 0
                
                analytics['type_breakdown'][row['cost_type']] += row['total_cost']
                analytics['total_cost'] += row['total_cost']
                analytics['total_operations'] += row['operation_count']
            
            return analytics
        except Exception as e:
            logger.error(f"❌ Error getting cost analytics: {e}")
            return {}
    
    async def get_emotional_state_transitions(self) -> List[Dict[str, Any]]:
        """Analyze emotional state transitions"""
        query = f"""
        WITH state_changes AS (
            SELECT 
                timestamp,
                emotional_state,
                balance_usd,
                LAG(emotional_state) OVER (ORDER BY timestamp) as previous_state,
                LAG(balance_usd) OVER (ORDER BY timestamp) as previous_balance
            FROM `{self.project_id}.{self.dataset_id}.{self.tables['treasury_snapshots']}`
            WHERE snapshot_type = 'hourly'
        )
        SELECT 
            timestamp,
            previous_state,
            emotional_state as new_state,
            previous_balance,
            balance_usd,
            balance_usd - previous_balance as balance_change
        FROM state_changes
        WHERE previous_state != emotional_state
        ORDER BY timestamp DESC
        LIMIT 50
        """
        
        try:
            results = self.client.query(query).result()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Error analyzing emotional transitions: {e}")
            return []
    
    # ========== YIELD OPTIMIZATION METHODS ==========
    
    async def insert_yield_performance(self, performance_data: Dict[str, Any]) -> bool:
        """Insert yield performance record"""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{self.tables['yield_performance']}"
            errors = self.client.insert_rows_json(table_id, [performance_data])
            
            if errors:
                logger.error(f"❌ Error inserting yield performance: {errors}")
                return False
            
            logger.info(f"✅ Yield performance record inserted: {performance_data.get('position_id')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error inserting yield performance: {e}")
            return False
    
    async def insert_rebalancing_event(self, event_data: Dict[str, Any]) -> bool:
        """Insert rebalancing event"""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{self.tables['rebalancing_events']}"
            errors = self.client.insert_rows_json(table_id, [event_data])
            
            if errors:
                logger.error(f"❌ Error inserting rebalancing event: {errors}")
                return False
            
            logger.info(f"✅ Rebalancing event inserted: {event_data.get('rebalance_id')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error inserting rebalancing event: {e}")
            return False
    
    async def insert_compound_event(self, event_data: Dict[str, Any]) -> bool:
        """Insert compound event"""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{self.tables['compound_events']}"
            errors = self.client.insert_rows_json(table_id, [event_data])
            
            if errors:
                logger.error(f"❌ Error inserting compound event: {errors}")
                return False
            
            logger.info(f"✅ Compound event inserted: {event_data.get('compound_id')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error inserting compound event: {e}")
            return False
    
    async def insert_risk_event(self, event_data: Dict[str, Any]) -> bool:
        """Insert risk event"""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{self.tables['risk_events']}"
            errors = self.client.insert_rows_json(table_id, [event_data])
            
            if errors:
                logger.error(f"❌ Error inserting risk event: {errors}")
                return False
            
            logger.info(f"✅ Risk event inserted: {event_data.get('event_id')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error inserting risk event: {e}")
            return False
    
    async def get_protocol_performance(self, protocol: str, chain: str, days: int = 30) -> Dict[str, Any]:
        """Get protocol performance analytics"""
        query = f"""
        SELECT 
            COUNT(DISTINCT position_id) as total_positions,
            AVG(realized_apy) as avg_realized_apy,
            AVG(advertised_apy) as avg_advertised_apy,
            AVG(realized_apy - advertised_apy) as avg_apy_variance,
            SUM(net_profit_usd) as total_profit,
            AVG(position_duration_hours / 24) as avg_position_days,
            COUNT(DISTINCT CASE WHEN exit_reason = 'risk_event' THEN position_id END) as risk_exits
        FROM `{self.project_id}.{self.dataset_id}.{self.tables['yield_performance']}`
        WHERE protocol = @protocol 
            AND chain = @chain
            AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("protocol", "STRING", protocol),
                bigquery.ScalarQueryParameter("chain", "STRING", chain),
            ]
        )
        
        try:
            results = self.client.query(query, job_config=job_config).result()
            return dict(next(results))
        except Exception as e:
            logger.error(f"❌ Error getting protocol performance: {e}")
            return {}
    
    async def get_gas_optimization_patterns(self, chain: str) -> List[Dict[str, Any]]:
        """Get gas optimization patterns for a chain"""
        query = f"""
        SELECT 
            hour_utc,
            day_of_week,
            AVG(gas_price_gwei) as avg_gas_price,
            MIN(gas_price_gwei) as min_gas_price,
            AVG(gas_price_usd) as avg_gas_cost_usd,
            COUNT(*) as sample_count
        FROM `{self.project_id}.{self.dataset_id}.{self.tables['gas_patterns']}`
        WHERE chain = @chain
            AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY hour_utc, day_of_week
        ORDER BY avg_gas_price ASC
        LIMIT 24
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("chain", "STRING", chain),
            ]
        )
        
        try:
            results = self.client.query(query, job_config=job_config).result()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Error getting gas patterns: {e}")
            return []
    
    async def get_effective_memories(self, min_profit_impact: float = 10.0) -> List[Dict[str, Any]]:
        """Get most effective memories by profit impact"""
        query = f"""
        SELECT 
            memory_id,
            category,
            content,
            importance_current,
            recall_count,
            decisions_influenced,
            profit_impact_usd,
            accuracy_score
        FROM `{self.project_id}.{self.dataset_id}.{self.tables['memory_effectiveness']}`
        WHERE profit_impact_usd >= {min_profit_impact}
            AND permanent_memory = true
        ORDER BY profit_impact_usd DESC
        LIMIT 50
        """
        
        try:
            results = self.client.query(query).result()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Error getting effective memories: {e}")
            return []