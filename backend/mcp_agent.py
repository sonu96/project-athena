from typing import Dict, Any
from mcp import MCPClient, Tool
from .mcp_tools import MemoryTool, TreasuryTool, MarketTool, DecisionTool, BaseBlockchainTool, Mem0Tool
from .models import DecisionContext, DecisionResult
from .treasury import TreasuryManager
from .memory import MemoryManager
from datetime import datetime
import os

class MCPDeFiAgent:
    """Simplified DeFi agent using MCP for tool orchestration with Base blockchain and Mem0"""
    
    def __init__(self):
        # Initialize core managers
        self.treasury_manager = TreasuryManager()
        self.memory_manager = MemoryManager(mem0_client=None)  # Will be injected
        
        # Initialize blockchain and memory tools
        self.base_tool = BaseBlockchainTool(
            rpc_url=os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
            private_key=os.getenv("AGENT_PRIVATE_KEY")
        )
        
        # Initialize Mem0 client (placeholder - will be injected)
        self.mem0_client = None
        self.mem0_tool = Mem0Tool(self.mem0_client)
        
        # Create MCP tools
        self.memory_tool = MemoryTool(self.memory_manager)
        self.treasury_tool = TreasuryTool(self.treasury_manager)
        self.market_tool = MarketTool()
        self.decision_tool = DecisionTool(
            self.memory_tool, 
            self.treasury_tool, 
            self.market_tool,
            self.base_tool,
            self.mem0_tool
        )
        
        # Initialize MCP client
        self.mcp_client = MCPClient()
        self.mcp_client.add_tool(self.memory_tool)
        self.mcp_client.add_tool(self.treasury_tool)
        self.mcp_client.add_tool(self.market_tool)
        self.mcp_client.add_tool(self.base_tool)
        self.mcp_client.add_tool(self.mem0_tool)
        self.mcp_client.add_tool(self.decision_tool)
    
    def set_mem0_client(self, mem0_client):
        """Set Mem0 client for persistent memory"""
        self.mem0_client = mem0_client
        self.mem0_tool = Mem0Tool(mem0_client)
        # Update the decision tool with new mem0 tool
        self.decision_tool = DecisionTool(
            self.memory_tool, 
            self.treasury_tool, 
            self.market_tool,
            self.base_tool,
            self.mem0_tool
        )
        # Update MCP client
        self.mcp_client.tools = []
        self.mcp_client.add_tool(self.memory_tool)
        self.mcp_client.add_tool(self.treasury_tool)
        self.mcp_client.add_tool(self.market_tool)
        self.mcp_client.add_tool(self.base_tool)
        self.mcp_client.add_tool(self.mem0_tool)
        self.mcp_client.add_tool(self.decision_tool)
    
    async def decide(self, context: DecisionContext) -> DecisionResult:
        """Make a decision using MCP orchestration with blockchain state"""
        
        # Add blockchain context if agent address is available
        decision_context = context.dict()
        if hasattr(context, 'agent_address') and context.agent_address:
            decision_context["agent_address"] = context.agent_address
        
        # MCP automatically handles the workflow with blockchain integration
        result = await self.mcp_client.run_agent({
            "context": decision_context,
            "task": "Make a yield farming decision based on current market conditions, agent state, and blockchain balance"
        })
        
        # Convert MCP result to DecisionResult
        return DecisionResult(
            action=result["action"],
            protocol=result.get("protocol"),
            amount=result.get("amount"),
            expected_yield=result.get("expected_yield"),
            risk_score=result["risk_score"],
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            treasury_impact=self._calculate_impact(result),
            blockchain_balance=result.get("blockchain_balance")
        )
    
    def _calculate_impact(self, result: Dict[str, Any]) -> float:
        """Calculate treasury impact of the decision"""
        if result["action"] == "HOLD":
            return 0.0
        elif result["action"] in ["CONSERVATIVE_YIELD", "AGGRESSIVE_YIELD"]:
            # Gas cost for transaction
            return -0.05  # $0.05 gas fee
        return 0.0
    
    async def record_experience(self, experience: Dict[str, Any]):
        """Record an experience using MCP memory tools"""
        
        # Record in local memory
        await self.mcp_client.run_tool("memory", {
            "operation": "record_survival",
            "event_type": experience["event_type"],
            "treasury_level": experience["treasury_level"],
            "action_taken": experience["action_taken"],
            "outcome": experience["outcome"]
        })
        
        # Also store in Mem0 for persistence
        if self.mem0_client:
            await self.mcp_client.run_tool("mem0", {
                "operation": "store_memory",
                "key": f"experience_{datetime.now().timestamp()}",
                "value": experience,
                "metadata": {"type": "experience", "timestamp": datetime.now().isoformat()}
            })
    
    async def get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state using MCP tools including blockchain"""
        
        treasury_state = await self.mcp_client.run_tool("treasury", {
            "operation": "get_state"
        })
        
        market_state = await self.mcp_client.run_tool("market", {
            "operation": "get_market_condition"
        })
        
        # Get blockchain state if agent address is configured
        blockchain_state = {}
        if hasattr(self, 'agent_address') and self.agent_address:
            blockchain_state = await self.mcp_client.run_tool("base_blockchain", {
                "operation": "get_balance",
                "address": self.agent_address
            })
        
        return {
            "treasury": treasury_state,
            "market": market_state,
            "blockchain": blockchain_state,
            "timestamp": datetime.now().isoformat()
        }
    
    async def simulate_cost(self, amount: float, reason: str):
        """Simulate a cost using MCP treasury tool"""
        
        await self.mcp_client.run_tool("treasury", {
            "operation": "deduct_cost",
            "amount": amount,
            "reason": reason
        })
    
    async def get_yield_opportunities(self) -> Dict[str, Any]:
        """Get yield opportunities using MCP market tool"""
        
        return await self.mcp_client.run_tool("market", {
            "operation": "get_yield_opportunities"
        })
    
    async def get_blockchain_balance(self, address: str) -> Dict[str, Any]:
        """Get blockchain balance using MCP Base tool"""
        
        return await self.mcp_client.run_tool("base_blockchain", {
            "operation": "get_balance",
            "address": address
        })
    
    async def search_memories(self, query: str, memory_type: str = "all") -> Dict[str, Any]:
        """Search memories using MCP Mem0 tool"""
        
        return await self.mcp_client.run_tool("mem0", {
            "operation": "search_memories",
            "query": query,
            "memory_type": memory_type
        })
    
    async def execute_blockchain_transaction(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute blockchain transaction using MCP Base tool"""
        
        return await self.mcp_client.run_tool("base_blockchain", {
            "operation": operation,
            **kwargs
        })

# Simplified FastAPI integration
class MCPAgentAPI:
    """Simplified API using MCP agent with blockchain and memory integration"""
    
    def __init__(self):
        self.agent = MCPDeFiAgent()
    
    async def make_decision(self, context: DecisionContext) -> DecisionResult:
        """Make a decision using MCP agent with blockchain integration"""
        return await self.agent.decide(context)
    
    async def get_state(self) -> Dict[str, Any]:
        """Get agent state including blockchain data"""
        return await self.agent.get_agent_state()
    
    async def record_experience(self, experience: Dict[str, Any]):
        """Record experience in both local and persistent memory"""
        await self.agent.record_experience(experience)
    
    async def simulate_cost(self, amount: float, reason: str):
        """Simulate cost"""
        await self.agent.simulate_cost(amount, reason)
    
    async def get_blockchain_balance(self, address: str) -> Dict[str, Any]:
        """Get blockchain balance"""
        return await self.agent.get_blockchain_balance(address)
    
    async def search_memories(self, query: str, memory_type: str = "all") -> Dict[str, Any]:
        """Search persistent memories"""
        return await self.agent.search_memories(query, memory_type)
    
    async def execute_blockchain_transaction(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute blockchain transaction"""
        return await self.agent.execute_blockchain_transaction(operation, **kwargs) 