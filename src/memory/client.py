"""
Mem0 Cloud Client

Handles all interactions with the Mem0 Cloud API for memory management.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from mem0 import MemoryClient as Mem0Client

from ..config import settings
from ..core.consciousness import Memory

logger = logging.getLogger(__name__)


class MemoryClient:
    """
    Client for Mem0 Cloud memory system
    
    Handles:
    - Memory formation
    - Memory search and retrieval
    - Pattern recognition support
    - Memory categorization
    """
    
    def __init__(self):
        self.client = Mem0Client(api_key=settings.mem0_api_key)
        self.user_id = settings.agent_id
        
        logger.info(f"✅ Mem0 client initialized for agent: {self.user_id}")
    
    async def add_memory(
        self,
        content: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a memory to Mem0 cloud
        
        Args:
            content: Memory content
            category: Memory category
            metadata: Additional metadata
            
        Returns:
            Memory creation result
        """
        try:
            # Prepare messages for Mem0
            messages = [
                {
                    "role": "assistant",
                    "content": content
                }
            ]
            
            # Prepare metadata
            full_metadata = {
                "category": category,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": self.user_id,
                **(metadata or {})
            }
            
            # Add to Mem0
            result = self.client.add(
                messages=messages,
                user_id=self.user_id,
                metadata=full_metadata
            )
            
            logger.debug(f"Memory added: {category} - {content[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return {"error": str(e)}
    
    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Memory]:
        """
        Search memories by query
        
        Args:
            query: Search query
            limit: Maximum results
            category: Filter by category
            
        Returns:
            List of Memory objects
        """
        try:
            # Build filters
            filters = {}
            if category:
                filters["category"] = category
            
            # Search Mem0
            results = self.client.search(
                query=query,
                user_id=self.user_id,
                limit=limit,
                filters=filters if filters else None
            )
            
            # Convert to Memory objects
            memories = []
            for result in results:
                memory = Memory(
                    id=result.get("id", ""),
                    content=result.get("memory", ""),
                    category=result.get("metadata", {}).get("category", "general"),
                    timestamp=self._parse_timestamp(result.get("metadata", {}).get("timestamp")),
                    importance=float(result.get("metadata", {}).get("importance", 0.5)),
                    usage_count=int(result.get("metadata", {}).get("usage_count", 0))
                )
                memories.append(memory)
            
            logger.debug(f"Found {len(memories)} memories for query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def get_all_memories(self) -> List[Memory]:
        """Get all memories for the agent"""
        try:
            results = self.client.get_all(user_id=self.user_id)
            
            # Convert to Memory objects
            memories = []
            for result in results:
                memory = Memory(
                    id=result.get("id", ""),
                    content=result.get("memory", ""),
                    category=result.get("metadata", {}).get("category", "general"),
                    timestamp=self._parse_timestamp(result.get("metadata", {}).get("timestamp")),
                    importance=float(result.get("metadata", {}).get("importance", 0.5)),
                    usage_count=int(result.get("metadata", {}).get("usage_count", 0))
                )
                memories.append(memory)
            
            logger.info(f"Retrieved {len(memories)} total memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            return []
    
    async def update_memory(
        self,
        memory_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Update memory metadata
        
        Args:
            memory_id: Memory ID
            metadata_updates: Metadata to update
            
        Returns:
            Success status
        """
        try:
            # Get current memory
            current = self.client.get(memory_id=memory_id)
            if not current:
                logger.warning(f"Memory {memory_id} not found")
                return False
            
            # Update metadata
            current_metadata = current.get("metadata", {})
            current_metadata.update(metadata_updates)
            current_metadata["last_accessed"] = datetime.utcnow().isoformat()
            
            # Update in Mem0
            self.client.update(
                memory_id=memory_id,
                metadata=current_metadata
            )
            
            logger.debug(f"Updated memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            return False
    
    async def increment_usage(self, memory_id: str) -> bool:
        """Increment memory usage count"""
        try:
            # Get current memory
            current = self.client.get(memory_id=memory_id)
            if not current:
                return False
            
            # Increment usage
            current_usage = int(current.get("metadata", {}).get("usage_count", 0))
            
            return await self.update_memory(
                memory_id,
                {"usage_count": current_usage + 1}
            )
            
        except Exception as e:
            logger.error(f"Failed to increment usage: {e}")
            return False
    
    async def get_memories_by_category(
        self,
        category: str,
        limit: int = 20
    ) -> List[Memory]:
        """Get memories by category"""
        return await self.search_memories(
            query="",  # Empty query to get all
            category=category,
            limit=limit
        )
    
    async def get_recent_memories(
        self,
        hours: int = 24,
        limit: int = 10
    ) -> List[Memory]:
        """Get recent memories within specified hours"""
        try:
            all_memories = await self.get_all_memories()
            
            # Filter by time
            cutoff = datetime.utcnow()
            recent = []
            
            for memory in all_memories:
                if memory.timestamp:
                    age = (cutoff - memory.timestamp).total_seconds() / 3600
                    if age <= hours:
                        recent.append(memory)
            
            # Sort by timestamp descending
            recent.sort(key=lambda m: m.timestamp or datetime.min, reverse=True)
            
            return recent[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent memories: {e}")
            return []
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return None
        
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None