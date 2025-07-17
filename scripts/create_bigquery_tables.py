#!/usr/bin/env python3
"""Create BigQuery tables for Athena Agent"""

from google.cloud import bigquery
import os

PROJECT_ID = "athena-defi-agent-1752635199"
DATASET_ID = "athena_analytics"

# Initialize client
client = bigquery.Client(project=PROJECT_ID)

# Define table schemas
pool_observations_schema = [
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("agent_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("pool_address", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("pool_type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("token0_symbol", "STRING"),
    bigquery.SchemaField("token1_symbol", "STRING"),
    bigquery.SchemaField("tvl_usd", "FLOAT64"),
    bigquery.SchemaField("volume_24h_usd", "FLOAT64"),
    bigquery.SchemaField("fee_apy", "FLOAT64"),
    bigquery.SchemaField("reward_apy", "FLOAT64"),
    bigquery.SchemaField("total_apy", "FLOAT64"),
    bigquery.SchemaField("reserve0", "FLOAT64"),
    bigquery.SchemaField("reserve1", "FLOAT64"),
    bigquery.SchemaField("lp_supply", "FLOAT64"),
]

agent_metrics_schema = [
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("agent_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("treasury_balance", "FLOAT64"),
    bigquery.SchemaField("emotional_state", "STRING"),
    bigquery.SchemaField("cycle_count", "INTEGER"),
    bigquery.SchemaField("memories_formed", "INTEGER"),
    bigquery.SchemaField("patterns_recognized", "INTEGER"),
    bigquery.SchemaField("total_cost", "FLOAT64"),
    bigquery.SchemaField("cost_per_decision", "FLOAT64"),
]

# Create tables
tables = [
    ("pool_observations", pool_observations_schema),
    ("agent_metrics", agent_metrics_schema),
    ("aerodrome_pools", pool_observations_schema),  # Alias for compatibility
]

for table_name, schema in tables:
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    table = bigquery.Table(table_id, schema=schema)
    
    try:
        table = client.create_table(table)
        print(f"Created table {table_id}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"Table {table_id} already exists")
        else:
            print(f"Error creating table {table_id}: {e}")

print("\nAll tables ready!")