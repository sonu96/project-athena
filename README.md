# 🤖 DeFi Yield Agent MVP 1.1

> A memory-driven DeFi yield optimization agent built with FastAPI + LangGraph + Mem0

## 🎯 MVP 1.1 Features

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

## 🏗️ Architecture

### **Tech Stack**
```python
# Backend
fastapi>=0.100.0        # API framework
langgraph>=0.1.0        # Agent workflows
mem0ai>=0.1.0           # Memory system
pydantic>=2.0.0         # Data validation

# Frontend (Next.js - Coming Soon)
next.js                  # React framework
typescript               # Type safety
tailwindcss              # Styling
```

### **Core Components**
```
backend/
├── models.py            # Data models
├── treasury.py          # Economic tracking
├── memory.py            # Memory management
├── agent.py             # LangGraph agent
└── main.py              # FastAPI app
```

## 🚀 Quick Start

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Configure Environment**
```bash
cp env.example .env
# Edit .env with your Mem0 API key
```

### **3. Run Backend**
```bash
cd backend
uvicorn main:app --reload
```

### **4. Test API**
```bash
curl http://localhost:8000/health
```

## 📊 API Endpoints

### **Agent Management**
```bash
GET /agent/state              # Get agent state
POST /agent/decide            # Make decision
```

### **Treasury Management**
```bash
GET /treasury/summary         # Get treasury summary
POST /treasury/deduct         # Deduct cost
POST /treasury/add            # Add revenue
```

### **Memory System**
```bash
POST /memory/record/survival  # Record survival event
POST /memory/record/strategy  # Record strategy performance
POST /memory/query            # Query memories
GET /memory/statistics        # Get memory stats
```

### **Real-time Updates**
```bash
WS /ws/agent                  # WebSocket for live updates
```

## 🧠 How It Works

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

### **4. LangGraph Workflow**
```python
# 5-step decision process
analyze_situation → query_memory → evaluate_options → make_decision → execute_action
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

## 🔧 Development

### **Running Tests**
```bash
# Test agent decision
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

### **Adding Memory**
```bash
# Record survival event
curl -X POST http://localhost:8000/memory/record/survival \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "low_treasury",
    "treasury_level": 75.0,
    "action_taken": "reduced_activity",
    "outcome": true
  }'
```

## 🚀 Next Steps (MVP 1.2)

### **Frontend Dashboard**
- Next.js dashboard
- Real-time visualizations
- Interactive controls

### **Market Integration**
- Real-time yield data
- Protocol APIs
- Market condition detection

### **Advanced Intelligence**
- Multi-protocol strategies
- Risk management
- Portfolio optimization

## 📄 License

MIT License - see LICENSE file for details.

---

**MVP 1.1: Memory Foundation Complete!** 🧠⚡

*The agent now has persistent memory, economic pressure, and survival instincts. Ready for the next phase of intelligence evolution!* 