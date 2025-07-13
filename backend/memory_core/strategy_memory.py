from typing import Dict, List, Optional
from mem0 import MemoryClient
from backend.models import MemoryEntry, MemoryType, MemoryQuery

class StrategyMemory:
    """Handles strategy performance tracking for the agent."""
    
    def __init__(self, mem0_client: MemoryClient, agent_id: str = "defi_yield_agent"):
        self.mem0 = mem0_client
        self.agent_id = agent_id

    def record_strategy_performance(self,
                                   strategy_name: str,
                                   success_rate: float,
                                   avg_yield: float,
                                   gas_cost: float,
                                   context: Dict = None):
        """Record yield strategy performance"""
        memory_data = {
            "strategy_name": strategy_name,
            "success_rate": success_rate,
            "avg_yield": avg_yield,
            "gas_cost": gas_cost,
            "context": context or {}
        }
        # Store in Mem0
        self.mem0.add_memory(
            messages=[{
                "role": "system",
                "content": f"Strategy performance: {strategy_name} success rate {success_rate}, "
                          f"avg yield {avg_yield}, gas cost {gas_cost}"
            }],
            user_id=self.agent_id,
            metadata={
                "category": "strategy",
                "importance": 0.8 if success_rate > 0.7 else 0.6,
                "success_rate": success_rate
            }
        )

    def get_yield_recommendations(self, 
                                 current_apy: float,
                                 protocol: str,
                                 market_condition: str) -> List[Dict]:
        """Get yield strategy recommendations based on memory"""
        query = f"What yield strategies worked for {protocol} with APY around {current_apy} in {market_condition} conditions?"
        memories = self.mem0.search_memories(
            query=query,
            user_id=self.agent_id,
            limit=3
        )
        return [memory for memory in memories if memory.get('metadata', {}).get('category') == 'strategy']
