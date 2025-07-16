# CLAUDE.md - Athena DeFi Agent Implementation Guide

This document serves as the comprehensive guide for implementing and maintaining the Athena DeFi Agent, an autonomous trading agent with emotional intelligence operating on Aerodrome Finance.

## Project Overview

Athena is an autonomous AI agent designed for leverage trading on Aerodrome Finance (BASE network). The agent features:
- **Emotional Intelligence**: Adaptive behavior based on treasury health
- **Memory-Driven Decisions**: Learns from every trade using Mem0
- **Survival Instincts**: Economic pressure drives intelligent behavior
- **Production Ready**: Built for 24/7 autonomous operation

## Architecture Philosophy

### Core Principles
1. **Consciousness-First Design**: The agent has a unified consciousness state that flows through a cognitive loop
2. **Emotional Risk Management**: Emotional states directly influence risk tolerance and trading behavior
3. **Continuous Learning**: Every observation and decision contributes to the agent's knowledge base
4. **Cost Awareness**: Every operation is tracked for cost, creating natural selection pressure

### Technology Stack
- **Language**: Python 3.10+
- **AI Framework**: LangGraph (sophisticated state machines)
- **LLM Integration**: Google Gemini via Vertex AI (Flash 2.0 → Gemini 1.5 Pro)
- **Memory System**: Mem0 Cloud API
- **Blockchain**: CDP AgentKit (BASE network)
- **Protocol**: Aerodrome Finance
- **Database**: Google Firestore (real-time) + BigQuery (analytics)
- **Monitoring**: LangSmith + Custom Dashboards
- **Deployment**: Google Cloud Run (containerized)

## V1 Implementation Plan (Observer Mode)

### Goals
- Build production-ready architecture
- Implement cognitive loop with emotional states
- Observe Aerodrome pools and form memories
- Learn patterns without executing trades
- Achieve stable 24/7 operation

### Project Structure
```
athena/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py                 # Main orchestrator
│   │   ├── consciousness.py         # Enhanced consciousness state
│   │   ├── emotions.py             # Emotional state management
│   │   └── treasury.py             # Financial tracking
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── client.py               # Mem0 Cloud integration
│   │   ├── patterns.py             # Pattern recognition
│   │   └── categories.py           # Memory categorization
│   ├── blockchain/
│   │   ├── __init__.py
│   │   ├── cdp_client.py           # CDP AgentKit wrapper
│   │   ├── wallet.py               # Wallet management
│   │   └── base_network.py         # BASE chain helpers
│   ├── aerodrome/
│   │   ├── __init__.py
│   │   ├── observer.py             # Pool observation (V1)
│   │   ├── pools.py                # Pool data structures
│   │   └── analytics.py            # Market analysis
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── cognitive_loop.py       # Main LangGraph workflow
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── sense.py            # Environment perception
│   │   │   ├── think.py            # Analysis with LLM
│   │   │   ├── feel.py             # Emotional processing
│   │   │   ├── decide.py           # Decision making
│   │   │   └── learn.py            # Memory formation
│   │   ├── routing.py              # Dynamic routing logic
│   │   └── llm_router.py           # Model selection logic
│   ├── database/
│   │   ├── __init__.py
│   │   ├── firestore_client.py     # Real-time database
│   │   ├── bigquery_client.py      # Analytics warehouse
│   │   └── schemas.py              # Data models
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── langsmith_config.py     # Tracing setup
│   │   ├── metrics.py              # Performance tracking
│   │   └── cost_tracker.py         # Cost monitoring
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py               # FastAPI application
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py           # Health checks
│   │   │   ├── agent.py            # Agent control
│   │   │   └── analytics.py        # Data endpoints
│   │   └── websocket.py            # Real-time updates
│   └── config/
│       ├── __init__.py
│       ├── settings.py             # Configuration management
│       └── constants.py            # System constants
├── cloud_functions/
│   ├── pool_collector/             # Collect pool data (15 min)
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── gas_tracker/                # Track gas prices (5 min)
│   │   ├── main.py
│   │   └── requirements.txt
│   └── daily_summary/              # Daily reports
│       ├── main.py
│       └── requirements.txt
├── deployment/
│   ├── Dockerfile                  # Container image
│   ├── cloudbuild.yaml            # CI/CD pipeline
│   ├── cloudrun.yaml              # Service configuration
│   └── .env.example               # Environment template
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/
│   ├── setup.py                   # Initial setup
│   ├── deploy.py                  # Deployment script
│   └── monitor.py                 # Local monitoring
├── docs/
│   ├── API.md                     # API documentation
│   ├── DEPLOYMENT.md              # Deployment guide
│   └── ARCHITECTURE.md            # Technical details
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

## Core Components

### 1. Enhanced Consciousness State
```python
class ConsciousnessState(BaseModel):
    # Identity
    agent_id: str
    timestamp: datetime
    cycle_count: int
    
    # Treasury
    treasury_balance: float
    daily_burn_rate: float
    days_until_bankruptcy: float
    
    # Emotional Intelligence
    emotional_state: EmotionalState  # Enum: DESPERATE, CAUTIOUS, STABLE, CONFIDENT
    emotional_intensity: float  # 0.0 to 1.0
    confidence_level: float
    
    # Observations
    market_data: Dict[str, Any]
    observed_pools: List[PoolObservation]
    
    # Memory
    recent_memories: List[Memory]
    active_patterns: List[Pattern]
    
    # Decision Context
    last_decision: Optional[Decision]
    pending_observations: List[str]
    
    # Operational
    total_cost: float
    llm_model: str
    errors: List[str]
    warnings: List[str]
```

### 2. Emotional State System
```python
Emotional States:
- DESPERATE (< 7 days runway): Survival mode, maximum conservation
- CAUTIOUS (< 20 days): Conservative operations, careful observation
- STABLE (< 90 days): Normal operations, balanced approach
- CONFIDENT (> 90 days): Growth mode, expanded operations

Each state affects:
- Observation frequency (4h → 2h → 1h → 30min)
- LLM model selection (Haiku → GPT-3.5 → Sonnet → Opus)
- Memory formation threshold
- Pattern recognition sensitivity
```

### 3. Cognitive Loop (LangGraph)
```
START → Sense → Think → Feel → Decide → Learn → END
         ↑                                        ↓
         └────────────(next cycle)────────────────┘

Parallel Operations in Sense:
- Fetch market data
- Check wallet balance
- Query recent memories
- Monitor gas prices
```

### 4. Memory Categories
```python
Memory Types:
1. Market Patterns: "USDC/ETH volume spikes on weekends"
2. Gas Patterns: "Gas cheapest 2-4 AM UTC Sundays"
3. Pool Behavior: "High APR pools often have high IL"
4. Timing Patterns: "US market open brings volatility"
5. Risk Patterns: "Leverage >2x risky in volatile markets"
6. Survival Memories: "Nearly bankrupt - must conserve"
```

## Database Architecture

### Firestore Collections
```
/agents/{agent_id}/
├── state                    # Current consciousness state
├── config                   # Agent configuration
└── health                   # Health metrics

/observations/{timestamp}/
├── pools                    # Observed pool states
├── market                   # Market conditions
└── gas                      # Gas prices

/memories/{agent_id}/
├── {memory_id}/
│   ├── content             # Memory content
│   ├── category            # Classification
│   ├── metadata            # Context
│   └── usage_stats         # How often used

/analytics/{date}/
├── decisions               # Daily decision log
├── costs                   # Cost breakdown
└── performance             # KPIs
```

### BigQuery Tables
```sql
-- Agent Performance
CREATE TABLE agent_metrics (
    timestamp TIMESTAMP,
    agent_id STRING,
    treasury_balance FLOAT64,
    emotional_state STRING,
    cycle_count INT64,
    memories_formed INT64,
    patterns_recognized INT64,
    total_cost FLOAT64,
    cost_per_decision FLOAT64
);

-- Observation Analytics
CREATE TABLE pool_observations (
    timestamp TIMESTAMP,
    pool_address STRING,
    pool_type STRING,
    tvl_usd FLOAT64,
    volume_24h_usd FLOAT64,
    fee_apy FLOAT64,
    reward_apy FLOAT64,
    observation_notes STRING
);

-- Memory Performance
CREATE TABLE memory_usage (
    timestamp TIMESTAMP,
    memory_id STRING,
    category STRING,
    times_accessed INT64,
    influenced_decisions INT64,
    success_correlation FLOAT64
);
```

## V1 Implementation Steps

### Phase 1: Core Setup (Days 1-3)
1. Initialize project structure
2. Set up GCP project and services
3. Configure CDP AgentKit
4. Integrate Mem0 Cloud API
5. Create basic consciousness state
6. Implement emotional state system

### Phase 2: Cognitive Loop (Days 4-7)
1. Build LangGraph workflow
2. Implement sense node (parallel data fetching)
3. Create think node (LLM analysis)
4. Build feel node (emotional processing)
5. Implement decide node (observation decisions)
6. Create learn node (memory formation)
7. Add dynamic routing logic

### Phase 3: Integrations (Days 8-10)
1. Complete CDP wallet integration
2. Build Aerodrome observer
3. Implement pool analytics
4. Create memory patterns system
5. Set up Firestore schemas
6. Configure BigQuery tables

### Phase 4: Production Ready (Days 11-14)
1. Build FastAPI server
2. Implement WebSocket for real-time updates
3. Create monitoring dashboards
4. Set up LangSmith tracing
5. Configure Cloud Run deployment
6. Implement cloud functions
7. Complete testing suite

## Deployment Configuration

### Environment Variables
```bash
# Required
AGENT_ID="athena-v1"
CDP_API_KEY_NAME="your-cdp-key"
CDP_API_KEY_SECRET="your-cdp-secret"
MEM0_API_KEY="your-mem0-key"
GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
GCP_PROJECT_ID="your-project-id"

# Optional
LANGSMITH_API_KEY="your-langsmith-key"
LANGSMITH_PROJECT="athena-v1"
OPENAI_API_KEY="your-openai-key"
ANTHROPIC_API_KEY="your-anthropic-key"

# Configuration
STARTING_TREASURY="100.0"
NETWORK="base-sepolia"  # Use testnet first
OBSERVATION_MODE="true"  # V1 doesn't trade
```

### Cloud Run Configuration
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: athena-agent
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/cpu-throttling: "false"
    spec:
      serviceAccountName: athena-agent-sa
      containerConcurrency: 1
      containers:
      - image: gcr.io/PROJECT_ID/athena-agent:latest
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
          requests:
            cpu: "1"
            memory: "2Gi"
        env:
        - name: ENV
          value: "production"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          periodSeconds: 30
      scaling:
        minScale: 1
        maxScale: 3
```

## Monitoring Strategy

### Key Metrics
1. **Health Metrics**
   - Agent uptime
   - Cognitive cycle frequency
   - Memory formation rate
   - Error rate

2. **Financial Metrics**
   - Treasury balance
   - Burn rate
   - Cost per cycle
   - Days until bankruptcy

3. **Learning Metrics**
   - Memories formed
   - Patterns recognized
   - Memory utilization
   - Decision quality score

### Alerts
```yaml
alerts:
  - name: "Low Treasury"
    condition: treasury_balance < 25
    severity: "warning"
    
  - name: "Critical Treasury"
    condition: treasury_balance < 10
    severity: "critical"
    
  - name: "High Error Rate"
    condition: error_rate > 0.1
    severity: "warning"
    
  - name: "Agent Down"
    condition: last_heartbeat > 5m
    severity: "critical"
```

## Testing Strategy

### Unit Tests
- Consciousness state transitions
- Emotional state calculations
- Memory formation logic
- Pattern recognition

### Integration Tests
- CDP wallet operations
- Mem0 API interactions
- Firestore operations
- LangGraph workflow execution

### E2E Tests
- Complete cognitive cycle
- Memory formation and retrieval
- Cost tracking accuracy
- WebSocket real-time updates

## Development Workflow

### Local Development
```bash
# Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp deployment/.env.example .env
# Edit .env with your credentials

# Run locally
python -m src.core.agent

# Run tests
pytest tests/

# Check code quality
black src/
flake8 src/
mypy src/
```

### Deployment Process
```bash
# Build container
docker build -t athena-agent .

# Test locally
docker run --env-file .env athena-agent

# Deploy to Cloud Run
gcloud run deploy athena-agent \
  --image gcr.io/PROJECT_ID/athena-agent:latest \
  --region us-central1 \
  --env-vars-file .env.yaml

# Deploy cloud functions
cd cloud_functions/pool_collector
gcloud functions deploy pool-collector \
  --runtime python310 \
  --trigger-schedule "*/15 * * * *"
```

## Future Versions Preview

### V2.0 - Aerodrome Trading
- Enable actual trading
- Leverage positions (1-3x)
- Risk management system
- P&L tracking

### V3.0 - Memory Enhancement
- Advanced pattern recognition
- Predictive analytics
- Strategy optimization
- Cross-pool correlations

### V4.0 - Risk Intelligence
- Multi-layer protection
- Liquidation prediction
- Portfolio optimization
- Hedging strategies

## Success Criteria for V1

### Technical
- [ ] 24/7 uptime achieved
- [ ] <500ms decision latency
- [ ] Zero fund loss
- [ ] All tests passing

### Learning
- [ ] 100+ memories formed
- [ ] 10+ patterns recognized
- [ ] Emotional states working correctly
- [ ] Cost optimization achieved

### Operational
- [ ] Production deployed
- [ ] Monitoring active
- [ ] Alerts configured
- [ ] Documentation complete

## Common Commands

```bash
# Start agent
python -m src.core.agent

# Run specific workflow
python -m src.workflows.cognitive_loop

# Check agent status
python scripts/monitor.py --status

# View logs
gcloud logging read "resource.labels.service_name=athena-agent" --limit=50

# Check costs
python scripts/monitor.py --costs

# Deploy update
./scripts/deploy.py --version=v1.0.1
```

## Troubleshooting

### Common Issues

1. **Memory API Errors**
   - Check MEM0_API_KEY is valid
   - Verify API quota not exceeded
   - Check network connectivity

2. **CDP Wallet Issues**
   - Ensure CDP keys are correct
   - Check wallet has gas funds
   - Verify network selection

3. **High Costs**
   - Review LLM model selection
   - Check cycle frequency
   - Verify parallel operations

4. **Deployment Failures**
   - Check Docker build logs
   - Verify environment variables
   - Review Cloud Run quotas

## Contact & Support

- GitHub Issues: [Project Repository]
- Documentation: This file and /docs
- Monitoring: LangSmith Dashboard

---

This document is the source of truth for Athena development. Update it as the project evolves.