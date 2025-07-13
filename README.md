# 🤖 Project Athena - DeFi Yield Agent

> An autonomous AI agent that manages DeFi yield farming strategies with real economic consequences, persistent memory, and survival instincts. Built with MCP (Model Context Protocol) for seamless blockchain and memory integration.

## 🌟 What Makes This Agent Different

### **Real Economic Consequences**
- Every action costs real money (gas fees, API calls, transactions)
- Agent manages its own wallet on Base blockchain
- Must survive economically or face "bankruptcy"

### **Persistent Learning**
- Uses Mem0 for semantic memory storage
- Learns from every decision and outcome
- Recalls past strategies in similar situations

### **Survival-Driven Intelligence**
- Adjusts risk tolerance based on treasury health
- More conservative when funds are low
- Aggressive strategies when well-funded

### **MCP Architecture**
- Clean tool interfaces for blockchain and memory
- Simplified agent logic through tool orchestration
- Easy to extend with new capabilities

## 🏗️ System Architecture

### **Core Components**

```
Project Athena/
├── backend/
│   ├── mcp_tools.py      # MCP tool implementations
│   ├── mcp_agent.py      # Intelligent agent with MCP integration
│   ├── memory.py         # Memory management system
│   ├── treasury.py       # Economic tracking
│   ├── models.py         # Data models
│   └── main.py           # FastAPI application
├── config/
│   └── project Docs/     # Project documentation
├── docs/
│   ├── mcp_integration.md      # MCP integration guide
│   └── junior_dev_guide.md     # Beginner-friendly guide
└── reports/
    └── mvp_1_1_completion_report.md
```

### **Technology Stack**

```python
# Core Framework
fastapi>=0.100.0         # API framework
mcp>=0.1.0               # Model Context Protocol

# Blockchain Integration
web3>=6.0.0              # Base blockchain connection
eth-account>=0.9.0       # Wallet management

# AI & Memory
openai>=1.0.0            # LLM integration
mem0ai>=0.1.0            # Persistent memory

# Infrastructure
redis>=4.0.0             # Caching
postgresql               # Database (optional)
uvicorn>=0.24.0          # ASGI server
```

## 🎯 MVP 1.1 Features (Completed)

### ✅ **Core Memory System**
- **Mem0 Integration**: Persistent, semantic memory storage
- **Memory Categories**: Survival, Strategy, Market, Protocol memories
- **Intelligent Recall**: Context-aware memory retrieval

### ✅ **Treasury Management**
- **Economic Tracking**: Real-time balance and cost monitoring
- **Survival Metrics**: Days until bankruptcy, burn rate analysis
- **Cost Attribution**: Detailed breakdown of all expenses

### ✅ **LangGraph Agent**
- **Decision Workflow**: 5-step decision process
- **Survival Pressure**: Risk tolerance based on treasury health
- **Memory-Driven**: All decisions informed by past experiences

### ✅ **FastAPI Backend**
- **REST API**: Complete CRUD operations
- **WebSocket**: Real-time agent state updates
- **Health Monitoring**: Comprehensive system status

## 🛠️ MCP Tools

The agent uses Model Context Protocol (MCP) tools for all operations:

### **1. BaseBlockchainTool**
Handles Base blockchain interactions:
- Get wallet balances
- Send transactions
- Approve tokens
- Check gas prices
- Monitor transaction status

### **2. Mem0Tool**
Manages persistent memory:
- Store experiences with semantic search
- Query past strategies
- Learn from outcomes
- Build pattern recognition

### **3. TreasuryTool**
Tracks economic health:
- Monitor balance changes
- Calculate burn rate
- Project days until bankruptcy
- Attribute costs to actions

### **4. MarketTool**
Analyzes DeFi opportunities:
- Fetch yield rates
- Compare protocols
- Assess risk levels
- Identify best opportunities

### **5. DecisionTool**
Orchestrates intelligent decisions:
- Evaluates options based on treasury
- Queries memory for similar situations
- Calculates risk-adjusted returns
- Executes chosen strategy

## 🚀 Quick Start

### **1. Prerequisites**
- Python 3.9+
- Base wallet with ETH for gas
- OpenAI API key
- Mem0 API key
- Redis (optional)
- PostgreSQL (optional)

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Configure Environment**
```bash
cp env.example .env
```

Edit `.env` with your credentials:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key
MEM0_API_KEY=your_mem0_api_key
BASE_RPC_URL=https://mainnet.base.org
AGENT_PRIVATE_KEY=your_private_key
AGENT_ADDRESS=your_wallet_address

# Optional
DATABASE_URL=postgresql://user:pass@localhost/defi_agent
REDIS_URL=redis://localhost:6379
INITIAL_TREASURY=1000.0
```

### **4. Run the Agent**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### **5. Verify Installation**
```bash
# Check health
curl http://localhost:8000/health

# Get agent state
curl http://localhost:8000/agent/state
```

## 📊 Complete API Reference

### **Agent Operations**
```bash
# Get current agent state with blockchain data
GET /agent/state

# Make intelligent decision
POST /agent/decide
{
  "current_treasury": 500,
  "market_condition": "stable",
  "available_protocols": ["aave", "compound"],
  "gas_price": 15.0,
  "risk_tolerance": 0.5
}
```

### **Blockchain Operations**
```bash
# Execute blockchain transaction via MCP
POST /blockchain/transaction
{
  "operation": "get_balance",
  "address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
}

# Check agent wallet balance
GET /blockchain/balance
```

### **Treasury Management**
```bash
# Get financial summary
GET /treasury/summary

# Track costs
POST /treasury/deduct
{
  "amount": 2.50,
  "category": "gas_fee",
  "description": "Aave deposit transaction"
}

# Record revenue
POST /treasury/add
{
  "amount": 50.0,
  "source": "yield_farming",
  "protocol": "aave"
}
```

### **Memory Operations**
```bash
# Store memory in Mem0
POST /memory/store
{
  "key": "strategy_2024_01",
  "value": {
    "protocol": "aave",
    "apy": 0.05,
    "success": true
  },
  "metadata": {
    "type": "strategy",
    "treasury_level": 500
  }
}

# Query memories
POST /memory/query
{
  "query": "successful yield strategies when treasury below 500",
  "memory_type": "strategy",
  "limit": 5
}

# Get memory statistics
GET /memory/statistics
```

### **Real-time Monitoring**
```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/agent');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Agent update:', data);
};
```

## 🧠 How the Agent Works

### **1. Memory-Driven Decisions**
```python
# Agent queries memory for similar situations
memories = memory_manager.get_survival_strategies(treasury_level=100)
# Uses past experiences to inform current decisions
```

### **2. Economic Pressure**
```python
# Every action has real costs
treasury.deduct_cost(0.05, "LLM API call")
treasury.deduct_cost(2.50, "Gas fee")
# Creates natural selection pressure
```

### **3. Survival-First Logic**
```python
# Risk tolerance based on treasury health
if treasury < 100:
    risk_tolerance = 0.1  # Very conservative
elif treasury < 500:
    risk_tolerance = 0.3  # Conservative
else:
    risk_tolerance = 0.7  # Aggressive
```

### **4. MCP-Orchestrated Workflow**
```python
# Decision flow with MCP tools
1. BaseBlockchainTool → Check wallet balance & gas prices
2. Mem0Tool → Query past experiences
3. MarketTool → Analyze current opportunities  
4. TreasuryTool → Calculate risk capacity
5. DecisionTool → Make intelligent choice
6. BaseBlockchainTool → Execute on-chain transaction
```

## 🎯 Decision Logic

### **Survival Mode (Treasury < $100)**
- **Action**: HOLD
- **Reasoning**: Treasury too low for active trading
- **Risk Score**: 0.1

### **Caution Mode (Treasury $100-$500)**
- **Action**: Conservative yield farming
- **Protocol**: Aave (safe)
- **Amount**: 30% of treasury
- **Risk Score**: 0.3

### **Aggressive Mode (Treasury > $500)**
- **Action**: Maximize yield
- **Protocol**: Compound (higher yield)
- **Amount**: 60% of treasury
- **Risk Score**: 0.6

## 📈 Success Metrics

### **Survival Metrics**
- Days until bankruptcy
- Treasury efficiency
- Cost per decision
- Memory utilization

### **Intelligence Metrics**
- Strategy success rate
- Learning velocity
- Pattern recognition
- Adaptation speed

## 🔧 Development Guide

### **Testing the Agent**

#### **1. Test Blockchain Integration**
```bash
# Check wallet balance
curl http://localhost:8000/blockchain/balance

# Execute test transaction
curl -X POST http://localhost:8000/blockchain/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "get_balance",
    "address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
  }'
```

#### **2. Test Memory System**
```bash
# Store a memory
curl -X POST http://localhost:8000/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "key": "test_strategy",
    "value": {"protocol": "aave", "apy": 0.05},
    "metadata": {"type": "strategy"}
  }'

# Query memories
curl -X POST http://localhost:8000/memory/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "aave strategies",
    "memory_type": "strategy"
  }'
```

#### **3. Test Decision Making**
```bash
# Trigger a decision
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

### **Monitoring Agent Behavior**

#### **Real-time WebSocket Monitoring**
```python
import asyncio
import websockets
import json

async def monitor_agent():
    uri = "ws://localhost:8000/ws/agent"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            event = json.loads(data)
            print(f"Agent Event: {event['type']}")
            print(f"Details: {event['data']}")
            print("-" * 50)

asyncio.run(monitor_agent())
```

### **Extending the Agent**

#### **Adding New MCP Tools**
```python
# backend/mcp_tools.py
class NewProtocolTool:
    async def execute(self, params: dict) -> dict:
        # Implement your tool logic
        return {"status": "success", "data": {...}}

# Register in mcp_agent.py
self.tools["new_protocol"] = NewProtocolTool()
```

## 🚀 Roadmap

### **MVP 1.2 - Frontend & Visualization**
- [ ] Next.js dashboard with real-time updates
- [ ] Agent decision visualization
- [ ] Memory exploration interface
- [ ] Treasury health monitoring
- [ ] Transaction history

### **MVP 1.3 - Advanced Market Integration**
- [ ] Real-time yield aggregation
- [ ] Multiple protocol support
- [ ] Cross-chain capabilities
- [ ] MEV protection
- [ ] Slippage optimization

### **MVP 2.0 - Multi-Agent System**
- [ ] Specialized sub-agents (Scout, Analyst, Executor)
- [ ] Agent collaboration protocols
- [ ] Distributed decision making
- [ ] Competitive agent dynamics

### **Future Vision**
- [ ] Self-improving strategies through reinforcement learning
- [ ] Community governance integration
- [ ] Plugin system for custom strategies
- [ ] Agent-to-agent communication protocol

## 🔒 Security Considerations

### **Private Key Management**
- Never commit private keys to version control
- Use environment variables for sensitive data
- Consider hardware wallet integration for production

### **Smart Contract Risks**
- Agent only interacts with verified protocols
- Implements slippage protection
- Gas price limits to prevent drain attacks

### **API Security**
- Rate limiting on all endpoints
- Authentication for production deployment
- Webhook validation for external integrations

## 📚 Documentation

- **[MCP Integration Guide](docs/mcp_integration.md)** - Detailed MCP tool documentation
- **[Junior Developer Guide](docs/junior_dev_guide.md)** - Beginner-friendly explanation
- **[MVP 1.1 Completion Report](reports/mvp_1_1_completion_report.md)** - Technical implementation details

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines (coming soon).

### **Areas for Contribution**
- New MCP tools for different protocols
- Memory optimization strategies
- Frontend dashboard components
- Testing and documentation

## 📄 License

MIT License - see LICENSE file for details.

---

**Project Athena** - *Where AI meets DeFi with real consequences* 🧠⚡

*An autonomous agent that must survive economically while learning and adapting to the DeFi landscape.* 