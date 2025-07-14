#!/bin/bash

# BigQuery table creation script for Project Athena
# Creates all required tables for memory and analytics storage

set -e

# Configuration
PROJECT_ID="project-athena-personal"
DATASET="athena_analytics"
LOCATION="US"

echo "Creating BigQuery tables for Project Athena..."

# Create dataset if it doesn't exist
echo "Ensuring dataset exists..."
bq mk --dataset --location=$LOCATION --description="Project Athena Analytics Data" $PROJECT_ID:$DATASET || echo "Dataset already exists"

# Create agent_decisions table
echo "Creating agent_decisions table..."
bq mk --table \
  --time_partitioning_field=timestamp \
  --time_partitioning_type=DAY \
  --clustering_fields=action,protocol \
  --description="Agent decision history with outcomes" \
  $PROJECT_ID:$DATASET.agent_decisions \
  decision_id:STRING,timestamp:TIMESTAMP,action:STRING,protocol:STRING,amount:NUMERIC,expected_yield:NUMERIC,actual_yield:NUMERIC,risk_score:NUMERIC,confidence:NUMERIC,treasury_before:NUMERIC,treasury_after:NUMERIC,gas_used:NUMERIC,market_condition:STRING,success:BOOLEAN,reasoning:STRING,memory_id:STRING,inserted_at:TIMESTAMP

# Create treasury_metrics table
echo "Creating treasury_metrics table..."
bq mk --table \
  --time_partitioning_field=timestamp \
  --time_partitioning_type=DAY \
  --description="Treasury health metrics over time" \
  $PROJECT_ID:$DATASET.treasury_metrics \
  timestamp:TIMESTAMP,balance:NUMERIC,daily_burn_rate:NUMERIC,weekly_burn_rate:NUMERIC,runway_days:NUMERIC,health_score:NUMERIC,risk_level:STRING,alert_count:INTEGER,spending_breakdown:RECORD,spending_breakdown.gas_fees:NUMERIC,spending_breakdown.api_calls:NUMERIC,spending_breakdown.failed_transactions:NUMERIC,spending_breakdown.decisions:NUMERIC,spending_breakdown.other:NUMERIC,inserted_at:TIMESTAMP

# Create memory_performance table
echo "Creating memory_performance table..."
bq mk --table \
  --time_partitioning_field=timestamp \
  --time_partitioning_type=DAY \
  --description="Memory system performance metrics" \
  $PROJECT_ID:$DATASET.memory_performance \
  timestamp:TIMESTAMP,total_memories:INTEGER,memories_by_type:RECORD,memories_by_type.decisions:INTEGER,memories_by_type.learnings:INTEGER,memories_by_type.market:INTEGER,memories_by_type.protocol:INTEGER,memories_by_type.survival:INTEGER,success_rate:NUMERIC,avg_confidence:NUMERIC,memory_health_score:NUMERIC,cleanup_count:INTEGER,storage_used_mb:NUMERIC,inserted_at:TIMESTAMP

# Create cost_analytics table
echo "Creating cost_analytics table..."
bq mk --table \
  --time_partitioning_field=date \
  --time_partitioning_type=DAY \
  --clustering_fields=category \
  --description="Cost breakdown and analytics" \
  $PROJECT_ID:$DATASET.cost_analytics \
  date:DATE,category:STRING,amount:NUMERIC,transaction_count:INTEGER,avg_cost_per_transaction:NUMERIC,subcategory_breakdown:JSON,optimization_applied:BOOLEAN,inserted_at:TIMESTAMP

# Create market_observations table
echo "Creating market_observations table..."
bq mk --table \
  --time_partitioning_field=timestamp \
  --time_partitioning_type=DAY \
  --description="Market conditions and protocol yields" \
  $PROJECT_ID:$DATASET.market_observations <<EOF
{
  "schema": [
    {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "market_condition", "type": "STRING", "mode": "NULLABLE"},
    {
      "name": "protocol_yields",
      "type": "RECORD",
      "mode": "REPEATED",
      "fields": [
        {"name": "protocol_name", "type": "STRING", "mode": "NULLABLE"},
        {"name": "apy", "type": "NUMERIC", "mode": "NULLABLE"},
        {"name": "tvl", "type": "NUMERIC", "mode": "NULLABLE"},
        {"name": "risk_score", "type": "NUMERIC", "mode": "NULLABLE"}
      ]
    },
    {"name": "gas_price", "type": "NUMERIC", "mode": "NULLABLE"},
    {"name": "volatility_index", "type": "NUMERIC", "mode": "NULLABLE"},
    {"name": "opportunities_found", "type": "INTEGER", "mode": "NULLABLE"},
    {"name": "inserted_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
  ]
}
EOF

echo "All tables created successfully!"

# List tables
echo ""
echo "Tables in $DATASET:"
bq ls --format=pretty $PROJECT_ID:$DATASET

# Create views for common queries
echo ""
echo "Creating useful views..."

# Recent decisions view
bq mk --view \
  --description="Recent agent decisions (last 7 days)" \
  --project_id=$PROJECT_ID \
  "${DATASET}.recent_decisions" \
  "SELECT * FROM \`$PROJECT_ID.$DATASET.agent_decisions\` 
   WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
   ORDER BY timestamp DESC"

# Treasury health view
bq mk --view \
  --description="Current treasury health status" \
  --project_id=$PROJECT_ID \
  "${DATASET}.treasury_health" \
  "SELECT * FROM \`$PROJECT_ID.$DATASET.treasury_metrics\`
   WHERE DATE(timestamp) = CURRENT_DATE()
   ORDER BY timestamp DESC
   LIMIT 1"

echo ""
echo "Setup complete! You can now start inserting data into these tables."
echo ""
echo "To query tables:"
echo "  bq query --use_legacy_sql=false 'SELECT * FROM \`$PROJECT_ID.$DATASET.agent_decisions\` LIMIT 10'"