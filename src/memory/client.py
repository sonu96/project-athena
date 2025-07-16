"""
Mem0 Cloud Client

Handles all interactions with the Mem0 Cloud API for memory management.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
import json

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
        """Initialize Mem0 Cloud client"""
        self.api_key = settings.mem0_api_key
        self.base_url = "https://api.mem0.ai/v1"
        self.user_id = settings.agent_id
        
        if not self.api_key:
            logger.warning("No Mem0 API key found, using mock memory")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"✅ Mem0 client initialized for agent: {self.user_id}")
    
    async def add_memory(
        self,
        agent_id: str,
        content: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a memory to Mem0 cloud
        
        Args:
            agent_id: Agent identifier
            content: Memory content
            category: Memory category
            metadata: Additional metadata
            
        Returns:
            Memory creation result
        """
        if not self.enabled:
            return {"success": False, "error": "Memory system disabled"}
            
        try:
            async with httpx.AsyncClient() as client:
                # Prepare payload
                payload = {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": content
                        }
                    ],
                    "user_id": agent_id,
                    "metadata": {
                        "category": category,
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent_id": agent_id,
                        **(metadata or {})
                    }
                }
                
                # Add to Mem0
                response = await client.post(
                    f"{self.base_url}/memories",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.debug(f"Memory added: {category} - {content[:50]}...")
                    return response.json()
                else:
                    logger.error(f"Failed to add memory: {response.status_code} - {response.text}")
                    return {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return {"error": str(e)}
    
    async def search_memories(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Memory]:
        """
        Search memories by query
        
        Args:
            agent_id: Agent identifier
            query: Search query
            limit: Maximum results
            category: Filter by category
            
        Returns:
            List of Memory objects
        """
        if not self.enabled:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                # Build params
                params = {
                    "query": query,
                    "user_id": agent_id,
                    "limit": limit
                }
                
                if category:
                    params["filters"] = json.dumps({"category": category})
                
                # Search Mem0
                response = await client.get(
                    f"{self.base_url}/memories/search",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Search failed: {response.status_code}")
                    return []
                
                results = response.json().get("results", [])
                
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
    
    async def get_all_memories(self, agent_id: str) -> List[Memory]:
        """Get all memories for the agent"""
        if not self.enabled:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/memories",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    params={"user_id": agent_id}
                )
                
                if response.status_code != 200:
                    logger.error(f"Get all failed: {response.status_code}")
                    return []
                
                results = response.json().get("memories", [])
                
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
        if not self.enabled:
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                # Update metadata
                payload = {
                    "metadata": {
                        **metadata_updates,
                        "last_accessed": datetime.utcnow().isoformat()
                    }
                }
                
                response = await client.patch(
                    f"{self.base_url}/memories/{memory_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.debug(f"Updated memory {memory_id}")
                    return True
                else:
                    logger.error(f"Update failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            return False
    
    async def increment_usage(self, memory_id: str) -> bool:
        """Increment memory usage count"""
        # For simplicity, just return True since we don't track usage in V1
        return True
    
    async def get_memories_by_category(
        self,
        agent_id: str,
        category: str,
        limit: int = 20
    ) -> List[Memory]:
        """Get memories by category"""
        return await self.search_memories(
            agent_id=agent_id,
            query="",  # Empty query to get all
            category=category,
            limit=limit
        )
    
    async def get_recent_memories(
        self,
        agent_id: str,
        hours: int = 24,
        limit: int = 10
    ) -> List[Memory]:
        """Get recent memories within specified hours"""
        try:
            all_memories = await self.get_all_memories(agent_id)
            
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