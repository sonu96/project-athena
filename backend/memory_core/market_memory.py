from typing import Dict, List, Optional
from mem0 import MemoryClient
from backend.models import MemoryEntry, MemoryType, MemoryQuery

class MarketMemory:
    """Handles market condition pattern storage and retrieval."""
    
    def __init__(self, mem0_client: MemoryClient, agent_id: str = "defi_yield_agent"):
        self.mem0 = mem0_client
        self.agent_id = agent_id

    def record_market_condition(self,
                               condition: str,
                               successful_actions: List[str],
                               failed_actions: List[str],
                               survival_rate: float,
                               context: Dict = None):
        """Record market condition response"""
        memory_data = {
            "condition": condition,
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "survival_rate": survival_rate,
            "context": context or {}
        }
        # Store in Mem0
        self.mem0.add_memory(
            messages=[{
                "role": "system",
                "content": f"Market condition: {condition} survival rate {survival_rate}. "
                          f"Successful: {successful_actions}, Failed: {failed_actions}"
            }],
            user_id=self.agent_id,
            metadata={
                "category": "market",
                "importance": 0.9 if survival_rate < 0.5 else 0.7,
                "survival_rate": survival_rate
            }
        )

    def get_market_insights(self, current_condition: str) -> List[Dict]:
        """Get market condition insights from memory"""
        query = f"What actions worked during {current_condition} market conditions?"
        memories = self.mem0.search_memories(
            query=query,
            user_id=self.agent_id,
            limit=5
        )
        return [memory for memory in memories if memory.get('metadata', {}).get('category') == 'market']
