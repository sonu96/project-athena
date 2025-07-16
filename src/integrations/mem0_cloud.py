"""
Mem0 Cloud Integration

Provides memory management capabilities for the Athena agent using Mem0's cloud service.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)

# Try to import Mem0 client
try:
    from mem0 import MemoryClient
    MEM0_AVAILABLE = True
except ImportError:
    logger.warning("Mem0 not available. Memory operations will be simulated.")
    MEM0_AVAILABLE = False


class Mem0CloudClient:
    """
    Client for interacting with Mem0 Cloud API
    
    Handles:
    - Memory storage and retrieval
    - Pattern recognition
    - Context-aware memory formation
    - Memory categorization
    """
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id or settings.agent_id
        self.client = None
        self.simulation_mode = False
        
        # Initialize Mem0 client
        if MEM0_AVAILABLE and settings.mem0_api_key:
            self._initialize_mem0()
        else:
            self.simulation_mode = True
            logger.info("🎮 Memory running in simulation mode")
    
    def _initialize_mem0(self):
        """Initialize Mem0 client"""
        try:
            self.client = MemoryClient(api_key=settings.mem0_api_key)
            logger.info("✅ Mem0 Cloud client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            self.simulation_mode = True
    
    async def add_memory(
        self, 
        content: str, 
        metadata: Dict[str, Any] = None,
        category: str = "general"
    ) -> Optional[str]:
        """
        Add a memory to Mem0
        
        Args:
            content: Memory content
            metadata: Additional metadata
            category: Memory category
            
        Returns:
            Memory ID if successful
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Would add memory: {content[:100]}...")
            return f"sim_memory_{datetime.now().timestamp()}"
        
        try:
            # Prepare memory data
            memory_data = {
                "text": content,
                "user_id": self.user_id,
                "metadata": {
                    "category": category,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }
            }
            
            # Add to Mem0
            result = self.client.add(
                messages=[{"role": "user", "content": content}],
                user_id=self.user_id,
                metadata=memory_data["metadata"]
            )
            
            if result and 'results' in result and len(result['results']) > 0:
                memory_id = result['results'][0].get('id')
                if memory_id:
                    logger.info(f"✅ Memory added: {memory_id}")
                    return memory_id
            
            logger.warning(f"Memory add returned unexpected result: {result}")
            return None
                
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return None
    
    async def search_memories(
        self, 
        query: str, 
        limit: int = 10,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories by query
        
        Args:
            query: Search query
            limit: Max results
            category: Filter by category
            
        Returns:
            List of matching memories
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Would search memories for: {query}")
            return [
                {
                    "id": f"sim_{i}",
                    "content": f"Simulated memory {i} matching '{query}'",
                    "score": 0.8 - (i * 0.1),
                    "metadata": {"category": category or "general"}
                }
                for i in range(min(3, limit))
            ]
        
        try:
            # Search Mem0
            results = self.client.search(
                query=query,
                user_id=self.user_id,
                limit=limit
            )
            
            memories = []
            for result in results:
                memory = {
                    "id": result.get("id"),
                    "content": result.get("text", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                }
                
                # Filter by category if specified
                if category and memory["metadata"].get("category") != category:
                    continue
                    
                memories.append(memory)
            
            logger.info(f"Found {len(memories)} memories for query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific memory by ID
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory data if found
        """
        if self.simulation_mode:
            return {
                "id": memory_id,
                "content": f"Simulated memory content for {memory_id}",
                "metadata": {"category": "general"}
            }
        
        try:
            result = self.client.get(memory_id, user_id=self.user_id)
            
            if result:
                return {
                    "id": result.get("id"),
                    "content": result.get("text", ""),
                    "metadata": result.get("metadata", {})
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {e}")
            return None
    
    async def update_memory(
        self, 
        memory_id: str, 
        content: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Update existing memory
        
        Args:
            memory_id: Memory to update
            content: New content
            metadata: New metadata
            
        Returns:
            Success status
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Would update memory: {memory_id}")
            return True
        
        try:
            update_data = {}
            if content:
                update_data["text"] = content
            if metadata:
                update_data["metadata"] = metadata
                
            result = self.client.update(
                memory_id=memory_id,
                data=update_data,
                user_id=self.user_id
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete memory
        
        Args:
            memory_id: Memory to delete
            
        Returns:
            Success status
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Would delete memory: {memory_id}")
            return True
        
        try:
            result = self.client.delete(memory_id, user_id=self.user_id)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False
    
    async def get_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all memories for the user
        
        Args:
            limit: Max memories to return
            
        Returns:
            List of all memories
        """
        if self.simulation_mode:
            return [
                {
                    "id": f"sim_all_{i}",
                    "content": f"Simulated memory {i}",
                    "metadata": {"category": "general"}
                }
                for i in range(min(5, limit))
            ]
        
        try:
            results = self.client.get_all(user_id=self.user_id, limit=limit)
            
            memories = []
            for result in results:
                memory = {
                    "id": result.get("id"),
                    "content": result.get("text", ""),
                    "metadata": result.get("metadata", {})
                }
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            return []
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics
        
        Returns:
            Memory usage statistics
        """
        if self.simulation_mode:
            return {
                "total_memories": 42,
                "categories": {"general": 20, "market": 15, "risk": 7},
                "simulation_mode": True
            }
        
        try:
            memories = await self.get_all_memories()
            
            # Count by category
            categories = {}
            for memory in memories:
                category = memory.get("metadata", {}).get("category", "unknown")
                categories[category] = categories.get(category, 0) + 1
            
            return {
                "total_memories": len(memories),
                "categories": categories,
                "simulation_mode": False
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get client status
        
        Returns:
            Status information
        """
        return {
            "connected": not self.simulation_mode,
            "simulation_mode": self.simulation_mode,
            "user_id": self.user_id,
            "mem0_available": MEM0_AVAILABLE
        }