import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from mem0 import MemoryClient
from backend.models import MemoryEntry, MemoryType, MemoryQuery

class SurvivalMemory:
    """Handles critical survival patterns for the agent."""
    
    def __init__(self, mem0_client: MemoryClient, agent_id: str = "defi_yield_agent"):
        self.mem0 = mem0_client
        self.agent_id = agent_id

    def record_survival_event(self, 
                            event_type: str,
                            treasury_level: float,
                            action_taken: str,
                            outcome: bool,
                            context: Dict = None):
        """Record critical survival events"""
        memory_data = {
            "event_type": event_type,
            "treasury_level": treasury_level,
            "action_taken": action_taken,
            "outcome": outcome,
            "context": context or {}
        }
        # Store in Mem0
        self.mem0.add_memory(
            messages=[{
                "role": "system",
                "content": f"Survival event: {event_type} at treasury level {treasury_level}. "
                          f"Action: {action_taken}. Success: {outcome}"
            }],
            user_id=self.agent_id,
            metadata={
                "category": "survival",
                "importance": 1.0 if not outcome else 0.8,
                "treasury_level": treasury_level
            }
        )

    def get_survival_strategies(self, current_treasury: float) -> List[Dict]:
        """Get relevant survival strategies based on current treasury level"""
        query = f"What survival strategies worked when treasury was around {current_treasury}?"
        memories = self.mem0.search_memories(
            query=query,
            user_id=self.agent_id,
            limit=5
        )
        return [memory for memory in memories if memory.get('metadata', {}).get('category') == 'survival'] 