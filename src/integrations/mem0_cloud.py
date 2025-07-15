"""
Mem0 Cloud integration for AI agent memory management
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging
import json
from mem0 import MemoryClient

from ..config.settings import settings

logger = logging.getLogger(__name__)


class Mem0CloudIntegration:
    """Manages AI agent memory using Mem0 Cloud API"""
    
    def __init__(self, firestore_client=None, bigquery_client=None):
        # Initialize Mem0 Cloud client
        self.client = MemoryClient(api_key=settings.mem0_api_key)
        self.agent_id = settings.agent_id
        
        # Memory categories for yield optimization
        self.categories = {
            'survival': 'survival_critical',
            'yield_patterns': 'yield_patterns',
            'risk_indicators': 'risk_indicators',
            'gas_patterns': 'gas_optimization',
            'compound_strategies': 'compound_optimization',
            'decision_outcomes': 'decision_outcomes'
        }
        
        logger.info(f"✅ Mem0 Cloud client initialized for agent: {self.agent_id}")
    
    async def initialize_memory_system(self) -> bool:
        """Initialize memory system with basic agent knowledge"""
        try:
            logger.info("🧠 Initializing Mem0 Cloud memory system...")
            
            # Test connection
            test_memory = await self.add_memory(
                "Agent initialized and ready to operate on BASE network",
                category="system",
                metadata={"importance": 0.5}
            )
            
            if "error" not in test_memory:
                logger.info("✅ Mem0 Cloud memory system initialized successfully")
                return True
            else:
                logger.error(f"❌ Failed to initialize Mem0 Cloud: {test_memory['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing Mem0 Cloud: {e}")
            return False
    
    async def add_memory(self, content: str, category: str = None, metadata: Dict = None) -> Dict:
        """Add a memory to Mem0 cloud"""
        try:
            # Prepare messages for memory creation
            messages = [
                {
                    "role": "assistant",
                    "content": content
                }
            ]
            
            # Add metadata
            full_metadata = {
                "category": category or "general",
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": self.agent_id,
                **(metadata or {})
            }
            
            # Add memory to Mem0 cloud
            result = self.client.add(
                messages=messages,
                user_id=self.agent_id,
                metadata=full_metadata
            )
            
            logger.info(f"✅ Memory added to Mem0 cloud: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error adding memory to Mem0 cloud: {e}")
            return {"error": str(e)}
    
    async def search_memories(self, query: str, category: str = None, limit: int = 10) -> List[Dict]:
        """Search memories in Mem0 cloud"""
        try:
            # Search with filters
            filters = {}
            if category:
                filters["category"] = category
            
            results = self.client.search(
                query=query,
                user_id=self.agent_id,
                limit=limit,
                filters=filters if filters else None
            )
            
            logger.info(f"Found {len(results)} memories for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching memories: {e}")
            return []
    
    async def get_all_memories(self) -> List[Dict]:
        """Get all memories for the agent"""
        try:
            memories = self.client.get_all(user_id=self.agent_id)
            logger.info(f"Retrieved {len(memories)} total memories")
            return memories
            
        except Exception as e:
            logger.error(f"❌ Error getting memories: {e}")
            return []
    
    async def update_memory(self, memory_id: str, content: str, metadata: Dict = None) -> Dict:
        """Update an existing memory"""
        try:
            result = self.client.update(
                memory_id=memory_id,
                content=content,
                metadata=metadata
            )
            logger.info(f"✅ Memory updated: {memory_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error updating memory: {e}")
            return {"error": str(e)}
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        try:
            self.client.delete(memory_id=memory_id)
            logger.info(f"✅ Memory deleted: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting memory: {e}")
            return False
    
    async def get_memory_history(self, memory_id: str) -> List[Dict]:
        """Get history of a specific memory"""
        try:
            history = self.client.history(memory_id=memory_id)
            return history
            
        except Exception as e:
            logger.error(f"❌ Error getting memory history: {e}")
            return []


# Quick test function
async def test_mem0_cloud():
    """Test Mem0 cloud connection"""
    try:
        mem0 = Mem0CloudIntegration()
        
        # Add a test memory
        test_memory = await mem0.add_memory(
            content="V1 Athena agent initialized with Compound V3 strategy",
            category="initialization",
            metadata={
                "version": "v1",
                "strategy": "compound_v3",
                "starting_capital": 30.0
            }
        )
        
        logger.info(f"Test memory added: {test_memory}")
        
        # Search for it
        results = await mem0.search_memories("Compound V3", category="initialization")
        logger.info(f"Search results: {results}")
        
        # Get all memories
        all_memories = await mem0.get_all_memories()
        logger.info(f"Total memories: {len(all_memories)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_mem0_cloud())