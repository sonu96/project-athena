# Memory Core Data Architecture

## Overview
This document outlines the data storage architecture for Project Athena's memory core system, including table schemas, data flow, and insertion frequencies.

## Storage Systems

### 1. Primary Memory Storage (Mem0 Cloud)
- **Purpose**: Primary persistent storage for all agent memories
- **Data Types**: Decisions, learnings, context, outcomes
- **Access Pattern**: Real-time read/write via API

### 2. BigQuery Analytics Tables
- **Purpose**: Historical analytics and reporting
- **Update Frequency**: Hourly aggregation
- **Retention**: 1 year for decisions, 90 days for metrics

### 3. Firestore Real-time Database
- **Purpose**: Live agent state and alerts
- **Update Frequency**: Real-time
- **Data Types**: Current state, active alerts, configurations

## Database Schema

### BigQuery Tables

#### 1. agent_decisions
```sql
CREATE TABLE `project-athena-personal.athena_analytics.agent_decisions` (
  decision_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  action STRING NOT NULL,
  protocol STRING,
  amount NUMERIC,
  expected_yield NUMERIC,
  actual_yield NUMERIC,
  risk_score NUMERIC,
  confidence NUMERIC,
  treasury_before NUMERIC,
  treasury_after NUMERIC,
  gas_used NUMERIC,
  market_condition STRING,
  success BOOLEAN,
  reasoning STRING,
  memory_id STRING,
  inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY action, protocol;
```

#### 2. treasury_metrics
```sql
CREATE TABLE `project-athena-personal.athena_analytics.treasury_metrics` (
  timestamp TIMESTAMP NOT NULL,
  balance NUMERIC NOT NULL,
  daily_burn_rate NUMERIC,
  weekly_burn_rate NUMERIC,
  runway_days NUMERIC,
  health_score NUMERIC,
  risk_level STRING,
  alert_count INTEGER,
  spending_breakdown STRUCT<
    gas_fees NUMERIC,
    api_calls NUMERIC,
    failed_transactions NUMERIC,
    decisions NUMERIC,
    other NUMERIC
  >,
  inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp);
```

#### 3. memory_performance
```sql
CREATE TABLE `project-athena-personal.athena_analytics.memory_performance` (
  timestamp TIMESTAMP NOT NULL,
  total_memories INTEGER,
  memories_by_type STRUCT<
    decisions INTEGER,
    learnings INTEGER,
    market INTEGER,
    protocol INTEGER,
    survival INTEGER
  >,
  success_rate NUMERIC,
  avg_confidence NUMERIC,
  memory_health_score NUMERIC,
  cleanup_count INTEGER,
  storage_used_mb NUMERIC,
  inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp);
```

#### 4. cost_analytics
```sql
CREATE TABLE `project-athena-personal.athena_analytics.cost_analytics` (
  date DATE NOT NULL,
  category STRING NOT NULL,
  amount NUMERIC NOT NULL,
  transaction_count INTEGER,
  avg_cost_per_transaction NUMERIC,
  subcategory_breakdown JSON,
  optimization_applied BOOLEAN DEFAULT FALSE,
  inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY category;
```

#### 5. market_observations
```sql
CREATE TABLE `project-athena-personal.athena_analytics.market_observations` (
  timestamp TIMESTAMP NOT NULL,
  market_condition STRING,
  protocol_yields STRUCT<
    protocol_name STRING,
    apy NUMERIC,
    tvl NUMERIC,
    risk_score NUMERIC
  > ARRAY,
  gas_price NUMERIC,
  volatility_index NUMERIC,
  opportunities_found INTEGER,
  inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp);
```

### Firestore Collections

#### agent_state
```javascript
{
  document_id: "current",
  current_balance: 1000.0,
  last_decision: "2024-12-20T10:30:00Z",
  last_decision_id: "dec_123456",
  active_positions: [
    {
      protocol: "aave",
      amount: 500,
      entry_time: "2024-12-20T10:30:00Z",
      expected_exit: "2024-12-21T10:30:00Z"
    }
  ],
  health_status: "healthy",
  risk_level: "medium",
  updated_at: "2024-12-20T10:35:00Z"
}
```

#### alerts
```javascript
{
  alert_id: "alert_789012",
  timestamp: "2024-12-20T10:35:00Z",
  level: "WARNING", // CRITICAL, WARNING, INFO
  metric: "treasury_balance",
  value: 450.0,
  threshold: 500.0,
  message: "Treasury balance below warning threshold",
  acknowledged: false,
  acknowledged_at: null,
  resolved: false,
  resolved_at: null
}
```

#### agent_config
```javascript
{
  document_id: "current",
  automation_enabled: true,
  schedules: {
    treasury_check: "0 9 * * *",
    market_scan: "0 */4 * * *",
    memory_cleanup: "0 0 * * 1"
  },
  thresholds: {
    min_treasury: 50.0,
    max_transaction: 100.0,
    max_daily_spend: 10.0
  },
  risk_parameters: {
    base_tolerance: 0.5,
    adjustment_factor: 0.1
  },
  updated_at: "2024-12-20T00:00:00Z"
}
```

## Data Flow & Insertion Frequencies

### Real-time Operations (Immediate)
1. **Decision Creation**
   - Mem0: Store decision memory
   - Firestore: Update agent_state
   - Local: Update in-memory caches

2. **Alert Generation**
   - Firestore: Create alert document
   - Local: Trigger webhooks/notifications

3. **State Changes**
   - Firestore: Update agent_state
   - Local: Broadcast via WebSocket

### Batch Operations

#### Every 5 Minutes
- Check treasury balance
- Update market conditions
- Monitor active positions

#### Hourly
- Aggregate decisions → BigQuery `agent_decisions`
- Calculate treasury metrics → BigQuery `treasury_metrics`
- Sync memory performance → BigQuery `memory_performance`

#### Every 4 Hours
- Market analysis → BigQuery `market_observations`
- Update protocol yields
- Scan for opportunities

#### Daily (9 AM UTC)
- Treasury health check
- Cost analytics → BigQuery `cost_analytics`
- Generate daily summary
- Check automation schedules

#### Weekly (Monday 00:00 UTC)
- Memory cleanup (remove old verbose memories)
- Performance analysis
- Cost optimization review
- Archive old alerts

## Memory Retention Policy

### Mem0 Storage
- **CRITICAL**: 365 days (treasury < $100, major losses)
- **IMPORTANT**: 90 days (significant decisions)
- **ROUTINE**: 30 days (normal operations)
- **VERBOSE**: 7 days (debug info, minor events)

### BigQuery
- **agent_decisions**: 1 year
- **treasury_metrics**: 90 days
- **memory_performance**: 90 days
- **cost_analytics**: 1 year
- **market_observations**: 30 days

### Firestore
- **agent_state**: Current only (no history)
- **alerts**: 30 days
- **agent_config**: Version history maintained

## Query Patterns

### Common Queries

1. **Recent Successful Strategies**
```sql
SELECT action, protocol, avg(actual_yield) as avg_yield
FROM `athena_analytics.agent_decisions`
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND success = TRUE
GROUP BY action, protocol
ORDER BY avg_yield DESC;
```

2. **Treasury Health Trend**
```sql
SELECT DATE(timestamp) as date, 
       AVG(balance) as avg_balance,
       MIN(balance) as min_balance,
       AVG(runway_days) as avg_runway
FROM `athena_analytics.treasury_metrics`
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY date
ORDER BY date DESC;
```

3. **Cost Analysis**
```sql
SELECT category, 
       SUM(amount) as total_cost,
       AVG(avg_cost_per_transaction) as avg_transaction_cost
FROM `athena_analytics.cost_analytics`
WHERE date > DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY category
ORDER BY total_cost DESC;
```

## Implementation Notes

1. **Idempotency**: All batch inserts use unique IDs to prevent duplicates
2. **Error Handling**: Failed inserts are retried with exponential backoff
3. **Cost Control**: Batch operations to minimize API calls
4. **Monitoring**: Cloud Monitoring alerts for failed jobs
5. **Security**: All sensitive data encrypted at rest

## Setup Instructions

### 1. Create BigQuery Dataset
```bash
bq mk --dataset --location=US project-athena-personal:athena_analytics
```

### 2. Create Tables
```bash
# Run each CREATE TABLE statement above
bq query --use_legacy_sql=false < create_tables.sql
```

### 3. Initialize Firestore
```bash
# Create collections via Firebase Console or CLI
firebase init firestore
```

### 4. Set Up Scheduled Jobs
- Use Cloud Scheduler for batch operations
- Configure Cloud Functions for data pipeline
- Set up monitoring alerts

## Cost Estimates

### Monthly Costs (Single User)
- BigQuery Storage: ~$0.20 (10GB)
- BigQuery Queries: ~$0.50 (100GB processed)
- Firestore: ~$0.10 (reads/writes)
- Cloud Functions: ~$0.50 (executions)
- **Total**: ~$1.30/month

### Optimization Tips
1. Use partitioning and clustering in BigQuery
2. Cache frequently accessed data
3. Batch writes to reduce API calls
4. Archive old data to Cloud Storage
5. Use materialized views for common queries