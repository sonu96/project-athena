"""
Mock memory system for when Mem0 is not available
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MockMemory:
    """Simple in-memory storage when Mem0 is not available"""
    
    def __init__(self):
        self.memories = []
        self.agent_id = "mock_agent"
        logger.info("📝 Using mock memory system (no persistence)")
    
    async def add(self, content: str, user_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add a memory"""
        memory = {
            "id": f"mock_{len(self.memories)}",
            "content": content,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.memories.append(memory)
        return memory
    
    async def search(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories (simple substring match)"""
        results = []
        query_lower = query.lower()
        
        for memory in self.memories:
            if memory["user_id"] == user_id and query_lower in memory["content"].lower():
                results.append(memory)
                
        return results[:limit]
    
    def get_all(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all memories for a user"""
        return [m for m in self.memories if m["user_id"] == user_id]