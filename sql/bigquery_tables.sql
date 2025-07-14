-- Athena DeFi Agent BigQuery Table Schemas
-- This file documents the table structures created programmatically

-- Market Data Table
-- Stores real-time market data collected every 15 minutes
CREATE OR REPLACE TABLE `athena_agent.market_data`
(
  timestamp TIMESTAMP NOT NULL,
  btc_price FLOAT64,
  eth_price FLOAT64,
  btc_24h_change FLOAT64,
  eth_24h_change FLOAT64,
  total_market_cap FLOAT64,
  defi_tvl FLOAT64,
  fear_greed_index INT64,
  gas_price_gwei FLOAT64,
  data_source STRING,
  data_quality_score FLOAT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY data_source;

-- Treasury Snapshots Table
-- Tracks agent's financial state over time
CREATE OR REPLACE TABLE `athena_agent.treasury_snapshots`
(
  timestamp TIMESTAMP NOT NULL,
  balance_usd FLOAT64 NOT NULL,
  daily_burn_rate FLOAT64,
  days_until_bankruptcy INT64,
  emotional_state STRING,
  risk_tolerance FLOAT64,
  confidence_level FLOAT64,
  snapshot_type STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY emotional_state;

-- Agent Decisions Table
-- Records all decisions made by the agent
CREATE OR REPLACE TABLE `athena_agent.agent_decisions`
(
  timestamp TIMESTAMP NOT NULL,
  decision_id STRING NOT NULL,
  decision_type STRING,
  market_condition STRING,
  treasury_state STRING,
  confidence_score FLOAT64,
  reasoning STRING,
  memory_context JSON,
  outcome STRING,
  cost_usd FLOAT64
)
PARTITION BY DATE(timestamp);

-- Cost Tracking Table
-- Detailed tracking of all operational costs
CREATE OR REPLACE TABLE `athena_agent.cost_tracking`
(
  timestamp TIMESTAMP NOT NULL,
  cost_type STRING NOT NULL,
  amount_usd FLOAT64 NOT NULL,
  description STRING,
  operation STRING,
  llm_tokens INT64,
  api_calls INT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY cost_type;

-- Memory Formations Table
-- Tracks memory creation and usage
CREATE OR REPLACE TABLE `athena_agent.memory_formations`
(
  timestamp TIMESTAMP NOT NULL,
  memory_id STRING NOT NULL,
  category STRING,
  importance FLOAT64,
  content STRING,
  metadata JSON,
  formation_trigger STRING,
  recall_count INT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY category;

-- Performance Metrics Table
-- System performance and operational metrics
CREATE OR REPLACE TABLE `athena_agent.performance_metrics`
(
  timestamp TIMESTAMP NOT NULL,
  metric_type STRING NOT NULL,
  value FLOAT64,
  unit STRING,
  context JSON
)
PARTITION BY DATE(timestamp)
CLUSTER BY metric_type;