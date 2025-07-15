-- Athena DeFi Agent - Yield Optimization Database Schema
-- Complete schema for DeFi yield optimization agent
-- Replaces observation-only schema with active yield management

-- =====================================================
-- YIELD PERFORMANCE TRACKING
-- =====================================================

-- Historical yield performance by position
CREATE OR REPLACE TABLE `athena_agent.yield_performance`
(
  timestamp TIMESTAMP NOT NULL,
  position_id STRING NOT NULL,
  protocol STRING NOT NULL,
  chain STRING NOT NULL,
  pool_address STRING,
  pool_name STRING,
  advertised_apy FLOAT64,
  realized_apy FLOAT64,
  position_duration_hours FLOAT64,
  total_earned_usd FLOAT64,
  total_gas_spent_usd FLOAT64,
  net_profit_usd FLOAT64,
  exit_reason STRING,
  market_condition STRING,
  emotional_state_on_entry STRING,
  emotional_state_on_exit STRING,
  memory_references ARRAY<STRING>
)
PARTITION BY DATE(timestamp)
CLUSTER BY protocol, chain;

-- =====================================================
-- REBALANCING EVENTS
-- =====================================================

-- Track all position rebalancing activities
CREATE OR REPLACE TABLE `athena_agent.rebalancing_events`
(
  rebalance_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  source_position_id STRING,
  target_position_id STRING,
  source_protocol STRING,
  target_protocol STRING,
  source_chain STRING,
  target_chain STRING,
  amount_moved_usd FLOAT64,
  gas_cost_usd FLOAT64,
  bridge_cost_usd FLOAT64,
  source_apy_at_exit FLOAT64,
  target_apy_at_entry FLOAT64,
  rebalance_reason STRING,
  success BOOLEAN,
  net_gain_loss_usd FLOAT64,
  execution_time_seconds INT64,
  memory_formation STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY success, source_chain, target_chain;

-- =====================================================
-- COMPOUND EVENTS
-- =====================================================

-- Track auto-compound operations
CREATE OR REPLACE TABLE `athena_agent.compound_events`
(
  compound_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  position_id STRING,
  protocol STRING,
  chain STRING,
  rewards_claimed_usd FLOAT64,
  rewards_claimed_tokens JSON,
  gas_cost_usd FLOAT64,
  compound_profitable BOOLEAN,
  days_since_last_compound FLOAT64,
  position_size_usd FLOAT64,
  gas_price_gwei FLOAT64,
  batched_with ARRAY<STRING>,
  compound_strategy STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY protocol, chain, compound_profitable;

-- =====================================================
-- RISK EVENTS
-- =====================================================

-- Track detected risks and mitigation actions
CREATE OR REPLACE TABLE `athena_agent.risk_events`
(
  event_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  event_type STRING, -- 'hack', 'rug', 'depeg', 'high_il', 'tvl_exodus'
  severity STRING, -- 'low', 'medium', 'high', 'critical'
  protocol STRING,
  chain STRING,
  detected_indicators JSON,
  action_taken STRING,
  position_exited BOOLEAN,
  loss_avoided_usd FLOAT64,
  false_positive BOOLEAN,
  memory_importance FLOAT64,
  lessons_learned STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY event_type, severity;

-- =====================================================
-- GAS OPTIMIZATION
-- =====================================================

-- Track gas patterns for optimization
CREATE OR REPLACE TABLE `athena_agent.gas_patterns`
(
  timestamp TIMESTAMP NOT NULL,
  chain STRING NOT NULL,
  hour_utc INT64,
  day_of_week STRING,
  gas_price_gwei FLOAT64,
  gas_price_usd FLOAT64,
  transaction_type STRING,
  success_rate FLOAT64,
  congestion_level STRING,
  special_event STRING, -- 'nft_mint', 'protocol_launch', etc
  memory_pattern STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY chain, hour_utc;

-- =====================================================
-- BRIDGE PERFORMANCE
-- =====================================================

-- Track cross-chain bridge operations
CREATE OR REPLACE TABLE `athena_agent.bridge_performance`
(
  bridge_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  bridge_protocol STRING,
  source_chain STRING,
  destination_chain STRING,
  asset STRING,
  amount_usd FLOAT64,
  quoted_cost_usd FLOAT64,
  actual_cost_usd FLOAT64,
  quoted_time_minutes INT64,
  actual_time_minutes INT64,
  slippage_percent FLOAT64,
  success BOOLEAN,
  failure_reason STRING,
  alternative_route_saved_usd FLOAT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY bridge_protocol, success;

-- =====================================================
-- MEMORY EFFECTIVENESS
-- =====================================================

-- Enhanced memory tracking with effectiveness metrics
CREATE OR REPLACE TABLE `athena_agent.memory_effectiveness`
(
  memory_id STRING NOT NULL,
  formation_timestamp TIMESTAMP NOT NULL,
  last_accessed TIMESTAMP,
  category STRING,
  content STRING,
  importance_initial FLOAT64,
  importance_current FLOAT64,
  recall_count INT64,
  decisions_influenced INT64,
  profit_impact_usd FLOAT64,
  accuracy_score FLOAT64,
  decay_rate FLOAT64,
  permanent_memory BOOLEAN
)
PARTITION BY DATE(formation_timestamp)
CLUSTER BY category, importance_current DESC;

-- =====================================================
-- ENHANCED AGENT DECISIONS
-- =====================================================

-- Enhanced decision tracking for yield optimization
CREATE OR REPLACE TABLE `athena_agent.agent_decisions`
(
  decision_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  decision_type STRING, -- 'enter_position', 'exit_position', 'rebalance', 'compound', 'risk_mitigation'
  decision_action STRING,
  reasoning TEXT,
  confidence_score FLOAT64,
  emotional_state STRING,
  treasury_balance_usd FLOAT64,
  market_condition STRING,
  memories_consulted ARRAY<STRING>,
  options_considered JSON,
  expected_outcome JSON,
  actual_outcome JSON,
  success BOOLEAN,
  lessons_learned STRING,
  memory_formed BOOLEAN,
  cost_incurred FLOAT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY decision_type, emotional_state, success;

-- =====================================================
-- PROTOCOL ANALYTICS
-- =====================================================

-- Track protocol-specific performance metrics
CREATE OR REPLACE TABLE `athena_agent.protocol_analytics`
(
  timestamp TIMESTAMP NOT NULL,
  protocol STRING NOT NULL,
  chain STRING NOT NULL,
  tvl_usd FLOAT64,
  tvl_24h_change_percent FLOAT64,
  unique_users_24h INT64,
  volume_24h_usd FLOAT64,
  avg_apy_stable FLOAT64,
  avg_apy_volatile FLOAT64,
  top_pool_address STRING,
  top_pool_apy FLOAT64,
  risk_score FLOAT64,
  hack_history BOOLEAN,
  audit_score FLOAT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY protocol, chain;

-- =====================================================
-- TREASURY SNAPSHOTS (ENHANCED)
-- =====================================================

-- Enhanced treasury tracking with DeFi positions
CREATE OR REPLACE TABLE `athena_agent.treasury_snapshots`
(
  timestamp TIMESTAMP NOT NULL,
  agent_id STRING NOT NULL,
  balance_usd FLOAT64 NOT NULL,
  balance_btc FLOAT64,
  total_value_locked FLOAT64,
  total_rewards_pending FLOAT64,
  daily_burn_rate FLOAT64,
  days_until_bankruptcy FLOAT64,
  emotional_state STRING,
  confidence_level FLOAT64,
  risk_tolerance FLOAT64,
  survival_mode_active BOOLEAN,
  positions_count INT64,
  chains_active ARRAY<STRING>,
  protocols_active ARRAY<STRING>,
  daily_yield_earned FLOAT64,
  significant_events JSON
)
PARTITION BY DATE(timestamp)
CLUSTER BY emotional_state;

-- =====================================================
-- COST TRACKING (ENHANCED)
-- =====================================================

-- Enhanced cost tracking with yield context
CREATE OR REPLACE TABLE `athena_agent.cost_tracking`
(
  timestamp TIMESTAMP NOT NULL,
  cost_type STRING NOT NULL, -- 'llm_cost', 'gas_cost', 'bridge_cost', 'api_cost'
  amount_usd FLOAT64 NOT NULL,
  description STRING,
  operation STRING,
  chain STRING,
  protocol STRING,
  position_id STRING,
  llm_tokens INT64,
  gas_units INT64,
  gas_price_gwei FLOAT64,
  api_calls INT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY cost_type, chain;

-- =====================================================
-- MARKET DATA (ENHANCED)
-- =====================================================

-- Enhanced market data with DeFi metrics
CREATE OR REPLACE TABLE `athena_agent.market_data`
(
  timestamp TIMESTAMP NOT NULL,
  btc_price FLOAT64,
  eth_price FLOAT64,
  btc_24h_change FLOAT64,
  eth_24h_change FLOAT64,
  btc_market_cap FLOAT64,
  eth_market_cap FLOAT64,
  total_market_cap FLOAT64,
  defi_tvl FLOAT64,
  defi_tvl_24h_change FLOAT64,
  stable_coin_supply FLOAT64,
  fear_greed_index INT64,
  gas_price_gwei_eth FLOAT64,
  gas_price_gwei_base FLOAT64,
  gas_price_gwei_arbitrum FLOAT64,
  active_addresses_btc INT64,
  active_addresses_eth INT64,
  defi_volume_24h FLOAT64,
  top_gainer_protocol STRING,
  top_gainer_apy FLOAT64,
  data_source STRING,
  collection_metadata JSON
)
PARTITION BY DATE(timestamp)
CLUSTER BY data_source;