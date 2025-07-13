# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Athena is a DeFi Yield Agent - an autonomous AI agent that manages DeFi yield farming strategies with real economic consequences, persistent memory, and survival instincts. The agent operates on Base blockchain and uses the Model Context Protocol (MCP) for clean tool orchestration.

## Key Technologies

- **FastAPI** - API framework (backend/main.py)
- **LangGraph** - AI agent orchestration
- **MCP (Model Context Protocol)** - Standardized tool interfaces (backend/mcp_tools.py, backend/mcp_agent.py)
- **Web3.py** - Base blockchain integration
- **Mem0** - Persistent memory storage
- **OpenAI** - LLM integration for agent intelligence

## Development Commands

### Running the Agent
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
```bash
cp env.example .env
# Edit .env with your API keys and configuration
```

### Testing API Endpoints
```bash
# Check health
curl http://localhost:8000/health

# Get agent state
curl http://localhost:8000/agent/state

# Make a decision
curl -X POST http://localhost:8000/agent/decide \
  -H "Content-Type: application/json" \
  -d '{
    "current_treasury": 500,
    "market_condition": "stable",
    "available_protocols": ["aave", "compound"],
    "gas_price": 15.0,
    "risk_tolerance": 0.5
  }'
```

## Architecture Overview

### MCP Tools Architecture
The agent uses MCP tools for all operations, providing clean separation of concerns:

1. **BaseBlockchainTool** (backend/mcp_tools.py:12-184)
   - Handles all Base blockchain interactions
   - Operations: get_balance, send_transaction, approve_token, etc.

2. **Mem0Tool** (backend/mcp_tools.py:186-266)
   - Manages persistent memory storage
   - Operations: store_memory, retrieve_memory, search_memories

3. **MemoryTool** (backend/mcp_tools.py:268-311)
   - Local memory operations for immediate access
   - Survival and strategy memory management

4. **TreasuryTool** (backend/mcp_tools.py:313-361)
   - Tracks agent's economic health
   - Calculates burn rate and survival metrics

5. **MarketTool** (backend/mcp_tools.py:363-403)
   - Fetches DeFi yield opportunities
   - Analyzes market conditions

6. **DecisionTool** (backend/mcp_tools.py:405-500)
   - Orchestrates all tools to make intelligent decisions
   - Considers treasury health, memories, and blockchain state

### Memory System
The agent has a dual memory system:
- **Local Memory** (backend/memory.py) - Fast access for immediate decisions
- **Mem0 Persistence** - Long-term storage via API

Memory categories:
- Survival memories (critical events)
- Strategy memories (successful approaches)
- Market memories (price patterns)
- Protocol memories (platform-specific knowledge)

### Decision Flow
1. Agent receives context (treasury level, market condition, etc.)
2. DecisionTool queries all relevant tools:
   - Blockchain balance from BaseBlockchainTool
   - Past experiences from Mem0Tool
   - Current treasury state from TreasuryTool
   - Market opportunities from MarketTool
3. Makes risk-adjusted decision based on survival pressure
4. Stores decision context in Mem0 for future learning

### API Structure (backend/main.py)
- `GET /agent/state` - Current agent state with blockchain data
- `POST /agent/decide` - Make intelligent decision
- `GET /treasury/summary` - Financial health metrics
- `POST /memory/query` - Search persistent memories
- `WebSocket /ws/agent` - Real-time agent updates

## Critical Files to Understand

1. **backend/mcp_agent.py** - Core MCP agent implementation
   - MCPDeFiAgent class orchestrates all tools
   - Handles decision making with blockchain context

2. **backend/mcp_tools.py** - All MCP tool implementations
   - Each tool has single responsibility
   - Clean interfaces for testing

3. **backend/treasury.py** - Economic survival logic
   - Tracks costs and revenue
   - Calculates days until bankruptcy

4. **backend/memory.py** - Memory management system
   - Categorizes and retrieves memories
   - Integrates with Mem0 for persistence

## Environment Variables Required

```bash
# Core APIs
OPENAI_API_KEY=your_openai_api_key
MEM0_API_KEY=your_mem0_api_key

# Blockchain
BASE_RPC_URL=https://mainnet.base.org
AGENT_PRIVATE_KEY=your_private_key
AGENT_ADDRESS=your_wallet_address

# Optional
DATABASE_URL=postgresql://user:pass@localhost/defi_agent
REDIS_URL=redis://localhost:6379
INITIAL_TREASURY=1000.0
```

## Key Design Principles

1. **Real Economic Consequences** - Every action costs real money (gas fees, API calls)
2. **Survival-Driven** - Agent adjusts risk based on treasury health
3. **Memory-Informed** - All decisions consider past experiences
4. **MCP Architecture** - Clean tool interfaces for maintainability

## Current Status

MVP 1.1 is complete with core backend infrastructure. The project is ready for MVP 1.2 which will add a frontend dashboard for visualization.

## Testing Approach

While no formal test files exist yet, the architecture supports easy testing:
- Mock MCP tools for unit tests
- Each tool can be tested independently
- API endpoints can be tested via curl commands

## Common Tasks

### Adding a New MCP Tool
1. Create tool class in backend/mcp_tools.py
2. Implement get_schema() and execute() methods
3. Register in MCPDeFiAgent.__init__() (backend/mcp_agent.py)

### Modifying Decision Logic
Edit DecisionTool.execute() in backend/mcp_tools.py:437-500

### Adding New Memory Type
1. Add category in backend/memory.py
2. Create storage method in MemoryManager
3. Update Mem0Tool if needed for persistence