# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Personal DeFi AI Agent project that creates an autonomous AI agent with economic survival pressure, memory-driven decision making, and market observation capabilities. The agent operates on the BASE network using CDP AgentKit, with data stored in Google Cloud Platform services.

## Technology Stack

- **Backend**: Python 3.9+, FastAPI
- **AI Orchestration**: LangGraph, LangSmith
- **Memory System**: Mem0
- **Database**: Google Firestore (operational), BigQuery (analytics)
- **Blockchain**: CDP AgentKit (BASE network)
- **Infrastructure**: Google Cloud Platform
- **AI Models**: Claude Sonnet 4, GPT-4 (configurable)
- **Container**: Docker

## Project Structure

```
defi-agent/
├── src/
│   ├── config/         # Settings and GCP configuration
│   ├── core/           # Agent, treasury, memory manager, market detector
│   ├── data/           # Database clients (Firestore, BigQuery)
│   ├── integrations/   # Mem0, CDP, LLM integrations
│   ├── workflows/      # LangGraph workflows for market analysis and decisions
│   └── utils/          # Cost tracking and alerts
├── cloud_functions/    # GCP cloud functions for scheduled tasks
├── tests/              # Unit, integration, and e2e tests
├── docker/             # Docker configuration files
├── deployment/         # Terraform, monitoring configs
└── sql/                # BigQuery table schemas

```

## Common Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy and configure)
cp .env.example .env
```

### Testing
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run end-to-end tests
pytest tests/e2e/

# Run with coverage
pytest --cov=src --cov-report=html

# Test LangGraph workflows specifically
pytest tests/integration/test_workflows.py -v

# Test LLM integrations
pytest tests/integration/test_llm_integration.py -v
```

### Local Development
```bash
# Run the agent locally
python -m src.core.agent

# Run with Docker
docker-compose up

# Build Docker image
docker build -t defi-agent .

# Run with LangSmith tracing enabled
LANGSMITH_API_KEY=your_key LANGSMITH_PROJECT="defi-agent-phase1" python -m src.core.agent

# View LangSmith traces
# Visit https://smith.langchain.com/ to view traces and debug workflows
```

### GCP Deployment
```bash
# Deploy cloud functions
cd cloud_functions/market_data_collector
gcloud functions deploy market-data-collector --runtime python39 --trigger-http --memory 128MB --timeout 60s

cd ../hourly_analysis
gcloud functions deploy hourly-analysis --runtime python39 --trigger-http --memory 256MB --timeout 300s

cd ../daily_summary
gcloud functions deploy daily-summary --runtime python39 --trigger-http --memory 256MB --timeout 300s
```

### Database Management
```bash
# Initialize Firestore database
python -c "from src.data.firestore_client import FirestoreClient; import asyncio; asyncio.run(FirestoreClient().initialize_database())"

# Initialize BigQuery dataset
python -c "from src.data.bigquery_client import BigQueryClient; import asyncio; asyncio.run(BigQueryClient().initialize_dataset())"
```

## Key Architecture Components

### Core Systems
1. **Agent Core** (`src/core/agent.py`): Main agent lifecycle management, coordinates all subsystems
2. **Treasury Manager** (`src/core/treasury.py`): Tracks agent's financial state, implements survival mechanisms
3. **Memory Manager** (`src/core/memory_manager.py`): Integrates with Mem0 for memory formation and retrieval
4. **Market Detector** (`src/core/market_detector.py`): Analyzes market conditions and identifies patterns
5. **LangGraph Workflows** (`src/workflows/`): Orchestrates complex multi-step operations using LangGraph
   - `market_analysis_flow.py`: Market condition analysis workflow
   - `decision_flow.py`: Decision-making workflow with memory integration

### Data Flow
1. Market data collected every 15 minutes via Cloud Function
2. Hourly analysis runs to detect market conditions via LangGraph workflow
3. Agent makes observations and forms memories using LLM calls
4. Daily summaries consolidate learning and update strategies
5. All costs tracked to maintain survival pressure

### LangGraph & LangSmith Integration
- **LangGraph**: Used for complex multi-step workflows with state management
  - Market analysis workflow with conditional branching
  - Decision workflows that incorporate memory queries
  - Survival mode activation flows
  - State persistence between workflow steps
  - Error handling and retry logic
- **LangSmith**: Monitoring and debugging for AI workflows
  - Trace all LangGraph workflow executions
  - Monitor LLM call performance and costs
  - Debug agent decision-making processes
  - Track memory formation and retrieval patterns
  - Analyze workflow performance metrics

### Critical Configurations
- Agent starts with $100 USD treasury
- Operates initially on base-sepolia testnet
- Survival mode activates when days_until_bankruptcy < 3
- Warning mode activates when days_until_bankruptcy < 5

## Important Phase 1 Constraints

- **Observer Mode Only**: Agent observes markets but does NOT execute real trades
- **Testnet Operations**: All blockchain interactions use base-sepolia testnet
- **Memory Formation Focus**: Primary goal is building memory and pattern recognition
- **30-Day Success Criteria**: Must run continuously for 30+ days while demonstrating learning

## Required Environment Variables

```bash
# GCP Configuration
GOOGLE_APPLICATION_CREDENTIALS  # Path to service account key
GCP_PROJECT_ID                  # GCP project ID
FIRESTORE_DATABASE             # Firestore database name
BIGQUERY_DATASET               # BigQuery dataset name

# API Keys
ANTHROPIC_API_KEY              # For Claude AI
OPENAI_API_KEY                 # For GPT-4 (optional)
CDP_API_KEY_NAME               # CDP AgentKit credentials
CDP_API_KEY_SECRET
MEM0_API_KEY                   # Memory system

# Agent Configuration
AGENT_STARTING_TREASURY        # Initial balance (default: 100.0)
AGENT_ID                       # Unique agent identifier
NETWORK                        # Blockchain network (base-sepolia)

# LangSmith Configuration
LANGSMITH_API_KEY              # LangSmith API key for tracing
LANGSMITH_PROJECT              # Project name for organizing traces
```

## Development Workflow

1. **Feature Development**: Create feature branch, implement with tests
2. **Memory Testing**: Ensure new features integrate with memory system
3. **Cost Tracking**: All operations must track costs appropriately
4. **Integration Testing**: Test with Firestore/BigQuery before deployment
5. **Monitoring**: Use GCP monitoring to track agent health post-deployment