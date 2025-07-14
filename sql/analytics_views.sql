-- Athena DeFi Agent Analytics Views
-- These views provide insights into agent behavior and performance

-- Daily Performance Summary View
CREATE OR REPLACE VIEW `athena_agent.daily_performance` AS
SELECT 
    DATE(timestamp) as date,
    -- Treasury Metrics
    LAST_VALUE(balance_usd) OVER (PARTITION BY DATE(timestamp) ORDER BY timestamp) as ending_balance,
    FIRST_VALUE(balance_usd) OVER (PARTITION BY DATE(timestamp) ORDER BY timestamp) as starting_balance,
    MIN(balance_usd) as lowest_balance,
    MAX(balance_usd) as highest_balance,
    -- Emotional State
    APPROX_TOP_COUNT(emotional_state, 1)[OFFSET(0)].value as dominant_emotional_state,
    COUNT(DISTINCT emotional_state) as emotional_state_changes,
    -- Costs
    SUM(amount_usd) as total_daily_cost,
    COUNT(*) as total_operations
FROM `athena_agent.treasury_snapshots` t
LEFT JOIN `athena_agent.cost_tracking` c ON DATE(t.timestamp) = DATE(c.timestamp)
GROUP BY date
ORDER BY date DESC;

-- Market Condition Analysis View
CREATE OR REPLACE VIEW `athena_agent.market_condition_summary` AS
WITH hourly_conditions AS (
    SELECT 
        DATE(timestamp) as date,
        EXTRACT(HOUR FROM timestamp) as hour,
        CASE 
            WHEN btc_24h_change > 5 AND eth_24h_change > 5 THEN 'strong_bull'
            WHEN btc_24h_change > 2 AND eth_24h_change > 2 THEN 'bull'
            WHEN btc_24h_change < -5 AND eth_24h_change < -5 THEN 'strong_bear'
            WHEN btc_24h_change < -2 AND eth_24h_change < -2 THEN 'bear'
            WHEN ABS(btc_24h_change) > 3 OR ABS(eth_24h_change) > 3 THEN 'volatile'
            ELSE 'neutral'
        END as market_condition,
        fear_greed_index,
        gas_price_gwei
    FROM `athena_agent.market_data`
)
SELECT 
    date,
    APPROX_TOP_COUNT(market_condition, 1)[OFFSET(0)].value as dominant_condition,
    AVG(fear_greed_index) as avg_fear_greed,
    AVG(gas_price_gwei) as avg_gas_price,
    COUNT(DISTINCT market_condition) as condition_changes
FROM hourly_conditions
GROUP BY date
ORDER BY date DESC;

-- Cost Efficiency View
CREATE OR REPLACE VIEW `athena_agent.cost_efficiency` AS
SELECT 
    DATE(c.timestamp) as date,
    c.cost_type,
    SUM(c.amount_usd) as total_cost,
    COUNT(*) as operation_count,
    AVG(c.amount_usd) as avg_cost_per_operation,
    SUM(c.llm_tokens) as total_tokens_used,
    -- Calculate cost per decision
    COUNT(DISTINCT d.decision_id) as decisions_made,
    SAFE_DIVIDE(SUM(c.amount_usd), COUNT(DISTINCT d.decision_id)) as cost_per_decision
FROM `athena_agent.cost_tracking` c
LEFT JOIN `athena_agent.agent_decisions` d 
    ON DATE(c.timestamp) = DATE(d.timestamp)
GROUP BY date, cost_type
ORDER BY date DESC, total_cost DESC;

-- Memory Usage Patterns View
CREATE OR REPLACE VIEW `athena_agent.memory_patterns` AS
SELECT 
    DATE(timestamp) as date,
    category,
    COUNT(*) as memories_formed,
    AVG(importance) as avg_importance,
    SUM(recall_count) as total_recalls,
    ARRAY_AGG(
        STRUCT(content, importance) 
        ORDER BY importance DESC 
        LIMIT 3
    ) as top_memories
FROM `athena_agent.memory_formations`
GROUP BY date, category
ORDER BY date DESC;

-- Emotional State Correlation View
CREATE OR REPLACE VIEW `athena_agent.emotional_correlation` AS
WITH state_metrics AS (
    SELECT 
        emotional_state,
        AVG(balance_usd) as avg_balance,
        AVG(daily_burn_rate) as avg_burn_rate,
        AVG(risk_tolerance) as avg_risk_tolerance,
        AVG(confidence_level) as avg_confidence,
        COUNT(*) as state_count
    FROM `athena_agent.treasury_snapshots`
    GROUP BY emotional_state
)
SELECT 
    s.*,
    AVG(d.confidence_score) as avg_decision_confidence,
    COUNT(DISTINCT d.decision_id) as decisions_in_state
FROM state_metrics s
LEFT JOIN `athena_agent.treasury_snapshots` t ON s.emotional_state = t.emotional_state
LEFT JOIN `athena_agent.agent_decisions` d 
    ON ABS(TIMESTAMP_DIFF(t.timestamp, d.timestamp, MINUTE)) < 30
GROUP BY 
    s.emotional_state, 
    s.avg_balance, 
    s.avg_burn_rate, 
    s.avg_risk_tolerance, 
    s.avg_confidence, 
    s.state_count;

-- Weekly Performance Trend View
CREATE OR REPLACE VIEW `athena_agent.weekly_performance` AS
SELECT 
    DATE_TRUNC(DATE(timestamp), WEEK) as week_start,
    -- Financial Metrics
    LAST_VALUE(balance_usd) OVER (PARTITION BY DATE_TRUNC(DATE(timestamp), WEEK) ORDER BY timestamp) as week_ending_balance,
    FIRST_VALUE(balance_usd) OVER (PARTITION BY DATE_TRUNC(DATE(timestamp), WEEK) ORDER BY timestamp) as week_starting_balance,
    -- Operational Metrics
    COUNT(DISTINCT DATE(timestamp)) as active_days,
    COUNT(DISTINCT decision_id) as total_decisions,
    SUM(cost_usd) as total_weekly_cost,
    -- Learning Metrics
    COUNT(DISTINCT memory_id) as memories_formed,
    AVG(confidence_score) as avg_confidence
FROM `athena_agent.treasury_snapshots` t
LEFT JOIN `athena_agent.agent_decisions` d USING(timestamp)
LEFT JOIN `athena_agent.cost_tracking` c USING(timestamp)
LEFT JOIN `athena_agent.memory_formations` m USING(timestamp)
GROUP BY week_start
ORDER BY week_start DESC;