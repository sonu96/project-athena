# Junior Developer Guide: DeFi Yield Agent MVP 1.1 with MCP Integration

> A beginner-friendly explanation of what we built and how it works

## 🎯 What We Built (In Simple Terms)

We built an **AI agent that learns to survive and make money** in the DeFi (Decentralized Finance) world. Think of it like a smart trading bot that:

1. **Remembers everything** - Every decision, success, and failure
2. **Faces real consequences** - Every action costs money
3. **Learns from experience** - Gets smarter over time
4. **Survives first, profits second** - Prioritizes staying alive over making money
5. **Connects to real blockchain** - Actually interacts with Base network
6. **Uses standardized tools** - MCP makes everything work together smoothly

## 🏗️ The Big Picture

### **Traditional Trading Bot vs Our Agent**

**Traditional Bot:**
```
Follow Rules → Make Decision → Execute → Reset
```

**Our Agent:**
```
Remember Past → Analyze Situation → Make Decision → Learn → Get Smarter
```

**With MCP Integration:**
```
MCP Tools → Base Blockchain → Mem0 Memory → Make Decision → Execute → Learn
```

## 🧠 How It Works (Step by Step)

### **Step 1: MCP Tool System**
```python
# The agent uses standardized tools for everything
base_tool = BaseBlockchainTool()  # Connects to Base blockchain
mem0_tool = Mem0Tool()           # Connects to persistent memory
treasury_tool = TreasuryTool()    # Manages money
memory_tool = MemoryTool()        # Local memory
```

**What this means:** Instead of complex code, the agent uses simple, standardized tools that all work together.

### **Step 2: Blockchain Connection**
```python
# The agent can check real blockchain balances
balance = await agent.get_blockchain_balance("0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6")
print(f"Agent has {balance['balance_eth']} ETH on Base")
```

**What this means:** The agent can see its real money on the Base blockchain and make decisions based on actual balances.

### **Step 3: Persistent Memory**
```python
# Store experiences in Mem0 (persistent memory)
await agent.record_experience({
    "event_type": "yield_farming",
    "action_taken": "stake_in_aave",
    "outcome": True,
    "blockchain_balance": {"balance": "1000000000000000000"}
})

# Search for similar past experiences
memories = await agent.search_memories("successful yield farming strategies")
```

**What this means:** The agent remembers everything that happened and can find similar situations from the past.

### **Step 4: Economic Pressure**
```python
# Every action costs real money
treasury.deduct_cost(0.05, "LLM API call")  # $0.05 for thinking
treasury.deduct_cost(2.50, "Gas fee")       # $2.50 for transaction
```

**What this means:** The agent can't just make unlimited decisions - each one costs money, so it has to be smart about when to act.

### **Step 5: Survival Logic**
```python
# The agent adapts based on how much money it has
if treasury < 100:
    action = "HOLD"  # Too poor, just wait
elif treasury < 500:
    action = "CONSERVATIVE"  # Be careful
else:
    action = "AGGRESSIVE"  # Go for it!
```

**What this means:** When the agent is broke, it's very conservative. When it's rich, it takes more risks.

## 🏗️ Technical Architecture (For Developers)

### **The Tech Stack We Chose**

**Why FastAPI?**
- Fast and modern Python web framework
- Automatic API documentation
- Great for building REST APIs

**Why MCP (Model Context Protocol)?**
- Standardized tool interfaces
- Easy to test and mock
- Reduces code complexity
- Better than manual LangGraph workflows

**Why Base Blockchain?**
- Ethereum L2 with low gas fees
- Perfect for DeFi operations
- Real economic consequences

**Why Mem0?**
- Persistent memory storage
- Semantic search (find similar memories)
- Perfect for AI agents that need to learn

### **The Core Files We Built**

#### **1. `backend/mcp_tools.py` - Standardized Tools**
```python
class BaseBlockchainTool(Tool):
    # Handles all Base blockchain operations
    async def execute(self, call):
        if call.operation == "get_balance":
            return self.w3.eth.get_balance(address)
        elif call.operation == "send_transaction":
            return self.send_transaction(to, amount)

class Mem0Tool(Tool):
    # Handles persistent memory operations
    async def execute(self, call):
        if call.operation == "store_memory":
            return await self.mem0.store(key, value)
        elif call.operation == "search_memories":
            return await self.mem0.search(query)
```

**What this does:** Provides standardized interfaces for blockchain and memory operations.

#### **2. `backend/mcp_agent.py` - Simplified Agent**
```python
class MCPDeFiAgent:
    def __init__(self):
        # Initialize MCP tools
        self.base_tool = BaseBlockchainTool()
        self.mem0_tool = Mem0Tool()
        self.treasury_tool = TreasuryTool()
        
        # MCP handles the workflow automatically
        self.mcp_client = MCPClient()
        self.mcp_client.add_tool(self.base_tool)
        self.mcp_client.add_tool(self.mem0_tool)
```

**What this does:** The agent uses MCP to orchestrate all tools automatically - much simpler than manual workflows.

#### **3. `backend/models.py` - Data Structures**
```python
class DecisionContext(BaseModel):
    current_treasury: float
    market_condition: str
    available_protocols: List[str]
    gas_price: float
    agent_address: str  # New: blockchain address
```

**What this does:** Defines the structure of our data so we know what information we're working with.

#### **4. `backend/treasury.py` - Money Management**
```python
class TreasuryManager:
    def deduct_cost(self, amount, reason):
        # Track every expense
        self.balance -= amount
        
    def get_survival_status(self):
        # Calculate if we're in danger
        if days_left < 1:
            return "CRITICAL"
```

**What this does:** Manages the agent's money, tracks expenses, and determines survival status.

#### **5. `backend/main.py` - API Server**
```python
app = FastAPI()

@app.post("/agent/decide")
async def make_decision(context: DecisionContext):
    # The agent makes a decision with blockchain context
    decision = agent.decide(context)
    return decision

@app.get("/blockchain/balance/{address}")
async def get_balance(address: str):
    # Get real blockchain balance
    return await agent.get_blockchain_balance(address)
```

**What this does:** Provides a web API so other applications can interact with our agent and blockchain.

## 🔄 How the Agent Makes Decisions (Updated)

### **The MCP-Enhanced Process:**

1. **Get Blockchain State** (`base_tool`)
   ```python
   # Check real wallet balance on Base
   balance = await base_tool.execute({
       "operation": "get_balance",
       "address": context.agent_address
   })
   ```

2. **Query Persistent Memory** (`mem0_tool`)
   ```python
   # Search for similar past experiences
   memories = await mem0_tool.execute({
       "operation": "search_memories",
       "query": "successful yield farming with low treasury",
       "memory_type": "experience"
   })
   ```

3. **Analyze Situation** (`treasury_tool`)
   ```python
   # Check how much money we have
   survival_status = treasury.get_survival_status()
   
   # Adjust risk tolerance based on money
   if survival_status == "CRITICAL":
       risk_tolerance = 0.1  # Very conservative
   ```

4. **Make Decision** (`decision_tool`)
   ```python
   # Choose the best action based on blockchain + memory + treasury
   if treasury < 100:
       decision = "HOLD"  # Too poor to trade
   elif successful_strategies:
       decision = "YIELD_FARM"  # Use proven strategy
   ```

5. **Execute Action** (`base_tool`)
   ```python
   # Actually do the chosen action on Base
   if decision.action == "YIELD_FARM":
       result = await base_tool.execute({
           "operation": "stake_tokens",
           "protocol": "aave",
           "amount": amount
       })
   ```

## 🎯 Key Concepts for Junior Developers

### **1. MCP - Model Context Protocol**
```python
# Instead of complex workflows, use standardized tools
tool = BaseBlockchainTool()
result = await tool.execute({
    "operation": "get_balance",
    "address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
})
```

**Why this matters:** MCP makes it easy to add new tools and test them individually.

### **2. Real Blockchain Integration**
```python
# The agent can see real money on Base
balance = await agent.get_blockchain_balance(address)
if float(balance['balance_eth']) < 0.1:
    action = "HOLD"  # Not enough ETH for gas
```

**Why this matters:** The agent faces real economic consequences, not just simulations.

### **3. Persistent Memory with Mem0**
```python
# Store experiences that last forever
await agent.record_experience({
    "event_type": "yield_farming",
    "action_taken": "stake_in_aave",
    "outcome": True,
    "blockchain_balance": balance
})

# Find similar past experiences
memories = await agent.search_memories("successful aave strategies")
```

**Why this matters:** The agent learns from every experience and can find similar situations.

### **4. Economic Pressure**
```python
# Every action has a real cost
gas_cost = calculate_gas_fee()
api_cost = 0.05  # LLM API call
if treasury.balance < (gas_cost + api_cost):
    raise InsufficientFundsError("Can't afford this action")
```

**Why this matters:** The agent can't just make unlimited decisions - each one costs money.

### **5. Survival-First Logic**
```python
# The agent prioritizes survival over profit
if days_until_bankruptcy < 7:
    strategy = "conservative_survival"
elif days_until_bankruptcy < 30:
    strategy = "balanced_growth"
else:
    strategy = "aggressive_profit"
```

**Why this matters:** The agent adapts its risk tolerance based on financial health.

## 🚀 How to Run the Project

### **Step 1: Set Up Environment**
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Edit .env with your keys
MEM0_API_KEY=your_mem0_key_here
BASE_RPC_URL=https://mainnet.base.org
AGENT_PRIVATE_KEY=your_private_key_here
AGENT_ADDRESS=your_wallet_address_here
```

### **Step 2: Run the Server**
```bash
cd backend
uvicorn main:app --reload
```

### **Step 3: Test the Integration**
```python
# Test blockchain connection
curl http://localhost:8000/blockchain/balance/0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6

# Test memory search
curl -X POST http://localhost:8000/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "successful yield farming", "memory_type": "experience"}'
```

## 🔧 New Features in This Version

### **1. Base Blockchain Integration**
- Real wallet balance checking
- Transaction execution
- Gas price monitoring
- Token approval and staking

### **2. MCP Tool System**
- Standardized interfaces
- Easy testing and mocking
- Reduced code complexity
- Better maintainability

### **3. Enhanced Memory System**
- Persistent storage with Mem0
- Semantic search capabilities
- Experience recording with blockchain data
- Historical pattern recognition

### **4. Improved Decision Making**
- Blockchain-aware decisions
- Memory-driven strategies
- Economic pressure simulation
- Survival-first logic

## 🎯 What Makes This Special

### **1. Real Economic Consequences**
The agent doesn't just simulate - it actually interacts with the Base blockchain and faces real costs.

### **2. Persistent Learning**
Every experience is stored in Mem0 and can be retrieved later to inform future decisions.

### **3. Standardized Architecture**
MCP makes it easy to add new tools and test them individually.

### **4. Survival-Driven Intelligence**
The agent prioritizes staying alive over making money, just like real organisms.

## 🚀 Next Steps

### **What's Coming Next:**
1. **Next.js Frontend** - Beautiful dashboard to monitor the agent
2. **Multi-Protocol Support** - Connect to more DeFi protocols
3. **Advanced Intelligence** - More sophisticated decision-making
4. **Social Features** - Share strategies between agents

### **Current Capabilities:**
- ✅ Real blockchain integration
- ✅ Persistent memory system
- ✅ Economic pressure simulation
- ✅ Survival-first logic
- ✅ Production-ready API
- ✅ MCP tool orchestration

---

**This is a living system that learns and adapts!** 🧠💰 