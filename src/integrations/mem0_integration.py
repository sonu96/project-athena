"""
Mem0 integration for AI agent memory management
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging
import json

try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    Memory = None

from ..config.settings import settings
from ..data.firestore_client import FirestoreClient
from ..data.bigquery_client import BigQueryClient
from .mock_memory import MockMemory

logger = logging.getLogger(__name__)


class Mem0Integration:
    """Manages AI agent memory using Mem0"""
    
    def __init__(self, firestore_client: FirestoreClient, bigquery_client: BigQueryClient):
        self.firestore = firestore_client
        self.bigquery = bigquery_client
        self.agent_id = settings.agent_id
        self.memory = None
        self._initialized = False
        
        # Check if we can use Mem0
        use_mock = False
        if not MEM0_AVAILABLE:
            logger.warning("⚠️ Mem0 not installed. Using mock memory system.")
            use_mock = True
        elif not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key":
            logger.warning("⚠️ Mem0 requires OpenAI API key for embeddings. Using mock memory system.")
            logger.info("   To enable full memory: Set OPENAI_API_KEY in your .env file")
            use_mock = True
        
        if use_mock:
            self.memory = MockMemory()
            self._initialized = True
            return
        
        try:
            # Initialize Mem0 with configuration
            from mem0.configs.base import MemoryConfig, VectorStoreConfig, LlmConfig, EmbedderConfig
            
            config = MemoryConfig(
                vector_store=VectorStoreConfig(
                    provider="qdrant",
                    config={
                        "collection_name": f"athena_agent_{settings.agent_id}",
                        "api_key": settings.mem0_api_key,
                        "url": settings.vector_db_url if settings.vector_db_url != "your_vector_db_url" else None,
                        "path": "/tmp/athena_qdrant" if settings.vector_db_url == "your_vector_db_url" else None
                    }
                ),
                llm=LlmConfig(
                    provider="openai",
                    config={
                        "model": "gpt-4",
                        "temperature": 0.1,
                        "api_key": settings.openai_api_key
                    }
                ),
                embedder=EmbedderConfig(
                    provider="openai",
                    config={
                        "model": "text-embedding-3-small",
                        "api_key": settings.openai_api_key
                    }
                ),
                history_db_path=f"/tmp/athena_memory_{settings.agent_id}.db"
            )
            
            self.memory = Memory(config)
            self._initialized = True
            logger.info("✅ Mem0 memory system initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Mem0: {e}")
            logger.info("   Agent will run without memory system")
        
        # Memory categories for yield optimization
        self.categories = {
            'survival': 'survival_critical',
            'yield_patterns': 'yield_patterns',
            'risk_indicators': 'risk_indicators',
            'gas_patterns': 'gas_optimization',
            'bridge_patterns': 'cross_chain_patterns',
            'protocol_behavior': 'protocol_specific',
            'compound_strategies': 'compound_optimization',
            'rebalance_triggers': 'rebalance_patterns',
            'decision_outcomes': 'decision_outcomes'
        }
        
        # Memory importance thresholds
        self.importance_levels = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3
        }
    
    async def initialize_memory_system(self) -> bool:
        """Initialize memory system with basic agent knowledge"""
        if not self.memory:
            logger.warning("Memory system not available - skipping initialization")
            return True  # Return True so agent can continue without memory
        
        try:
            # Core survival knowledge
            survival_memories = [
                {
                    "content": "When treasury drops below $30, immediately activate emergency mode: reduce all non-essential costs, switch to conservative strategies, and focus on capital preservation.",
                    "metadata": {
                        "category": "survival_critical",
                        "importance": 1.0,
                        "context": "treasury_emergency"
                    }
                },
                {
                    "content": "Daily burn rate above $15 is unsustainable. If burn rate exceeds this threshold, reduce observation frequency and limit expensive operations.",
                    "metadata": {
                        "category": "survival_critical",
                        "importance": 0.9,
                        "context": "cost_management"
                    }
                },
                {
                    "content": "In desperate emotional state, risk tolerance should be minimal. Focus on preservation over growth.",
                    "metadata": {
                        "category": "survival_critical",
                        "importance": 1.0,
                        "context": "emotional_response"
                    }
                }
            ]
            
            # Yield optimization knowledge
            yield_memories = [
                {
                    "content": "Stable coin pools typically offer 5-15% APY with minimal impermanent loss risk. Prioritize these in risk-averse states.",
                    "metadata": {
                        "category": "yield_patterns",
                        "importance": 0.7,
                        "context": "stable_yields"
                    }
                },
                {
                    "content": "Advertised APYs often include reward tokens. Real yields are typically 20-30% lower after accounting for price volatility.",
                    "metadata": {
                        "category": "yield_patterns",
                        "importance": 0.8,
                        "context": "apy_reality"
                    }
                },
                {
                    "content": "Compound rewards when they exceed $10 or 5% of position value. Smaller amounts aren't worth the gas costs.",
                    "metadata": {
                        "category": "compound_optimization",
                        "importance": 0.6,
                        "context": "compound_threshold"
                    }
                }
            ]
            
            # Risk indicator knowledge
            risk_memories = [
                {
                    "content": "TVL dropping 30% in 24 hours is a strong exit signal. This pattern preceded 3 major protocol exploits.",
                    "metadata": {
                        "category": "risk_indicators",
                        "importance": 0.95,
                        "context": "tvl_exodus"
                    }
                },
                {
                    "content": "Unusually high APYs (>100%) often indicate unsustainable tokenomics or high risk. Approach with extreme caution.",
                    "metadata": {
                        "category": "risk_indicators",
                        "importance": 0.85,
                        "context": "unsustainable_yields"
                    }
                }
            ]
            
            # Gas optimization knowledge
            gas_memories = [
                {
                    "content": "Base chain gas is typically 70% cheaper between 2-5 AM UTC on weekends. Schedule non-urgent operations accordingly.",
                    "metadata": {
                        "category": "gas_optimization",
                        "importance": 0.7,
                        "context": "base_gas_patterns"
                    }
                },
                {
                    "content": "Batch similar operations together. Multiple position updates in one transaction save 40-60% on gas costs.",
                    "metadata": {
                        "category": "gas_optimization",
                        "importance": 0.6,
                        "context": "batching_strategy"
                    }
                }
            ]
            
            # Bridge pattern knowledge
            bridge_memories = [
                {
                    "content": "Stargate offers reliable USDC bridging between chains. Sunday nights typically have lowest bridge congestion.",
                    "metadata": {
                        "category": "cross_chain_patterns",
                        "importance": 0.6,
                        "context": "bridge_timing"
                    }
                },
                {
                    "content": "Cross-chain arbitrage needs >5% APY difference to be profitable after bridge costs and risks.",
                    "metadata": {
                        "category": "cross_chain_patterns",
                        "importance": 0.7,
                        "context": "arbitrage_threshold"
                    }
                }
            ]
            
            # Store initial memories
            all_memories = (survival_memories + yield_memories + risk_memories + 
                          gas_memories + bridge_memories)
            
            for memory_data in all_memories:
                await self.add_memory(
                    content=memory_data["content"],
                    metadata=memory_data["metadata"]
                )
            
            # Log initialization
            await self.firestore.log_system_event(
                "memory_system_initialized",
                {
                    "initial_memories": len(all_memories),
                    "categories": list(self.categories.values())
                }
            )
            
            logger.info(f"✅ Mem0 memory system initialized with {len(all_memories)} core memories")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing memory system: {e}")
            return False
    
    async def add_memory(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add a new memory to the agent's knowledge base"""
        try:
            # Ensure required metadata
            if 'category' not in metadata:
                metadata['category'] = 'general'
            if 'importance' not in metadata:
                metadata['importance'] = 0.5
            if 'timestamp' not in metadata:
                metadata['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Add memory to Mem0 or MockMemory
            if isinstance(self.memory, MockMemory):
                result = await self.memory.add(
                    content=content,
                    user_id=self.agent_id,
                    metadata=metadata
                )
            else:
                result = self.memory.add(
                    messages=content,
                    user_id=self.agent_id,
                metadata=metadata
            )
            
            memory_id = result.get('id', '')
            
            # Store in BigQuery for analytics
            await self.bigquery.client.insert_rows_json(
                f"{settings.gcp_project_id}.{settings.bigquery_dataset}.memory_formations",
                [{
                    "timestamp": metadata['timestamp'],
                    "memory_id": memory_id,
                    "category": metadata['category'],
                    "importance": metadata['importance'],
                    "content": content,
                    "metadata": json.dumps(metadata),
                    "formation_trigger": metadata.get('trigger', 'manual'),
                    "recall_count": 0
                }]
            )
            
            logger.info(f"✅ Memory added: {memory_id} (importance: {metadata['importance']})")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Error adding memory: {e}")
            return ""
    
    async def query_memories(self, query: str, category: Optional[str] = None, 
                           limit: int = 5) -> List[Dict[str, Any]]:
        """Query relevant memories for decision making"""
        try:
            # Build filters
            filters = {}
            if category:
                filters['category'] = category
            
            # Search memories
            results = self.memory.search(
                query=query,
                user_id=self.agent_id,
                limit=limit,
                filters=filters
            )
            
            memories = []
            for result in results:
                memory = {
                    "id": result.get("id", ""),
                    "content": result.get("memory", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0)
                }
                memories.append(memory)
                
                # Update recall count in BigQuery
                self.bigquery.client.query(f"""
                    UPDATE `{settings.gcp_project_id}.{settings.bigquery_dataset}.memory_formations`
                    SET recall_count = recall_count + 1
                    WHERE memory_id = '{memory['id']}'
                """)
            
            return memories
            
        except Exception as e:
            logger.error(f"❌ Error querying memories: {e}")
            return []
    
    async def update_memory_from_experience(self, experience: Dict[str, Any]) -> bool:
        """Update memory based on agent experience"""
        try:
            # Determine memory content based on experience type
            if experience["type"] == "survival_event":
                content = f"Treasury survival event: {experience['description']}. "\
                         f"Outcome: {experience['outcome']}. "\
                         f"Key lesson: {experience['lesson']}"
                metadata = {
                    "category": "survival_critical",
                    "importance": 1.0,
                    "treasury_level": experience.get("treasury_level", 0),
                    "trigger": "survival_event"
                }
                
            elif experience["type"] == "market_observation":
                content = f"Market condition {experience['condition']} observed. "\
                         f"Indicators: {experience['indicators']}. "\
                         f"Appropriate response: {experience['response']}"
                metadata = {
                    "category": "market_patterns",
                    "importance": 0.7,
                    "market_metrics": experience.get("metrics", {}),
                    "trigger": "market_observation"
                }
                
            elif experience["type"] == "protocol_interaction":
                content = f"Protocol {experience['protocol']} interaction. "\
                         f"Action: {experience['action']}. "\
                         f"Result: {experience['result']}"
                metadata = {
                    "category": "protocol_behavior",
                    "importance": 0.6,
                    "protocol_name": experience['protocol'],
                    "success": experience.get("success", True),
                    "trigger": "protocol_interaction"
                }
                
            elif experience["type"] == "decision_outcome":
                content = f"Decision '{experience['decision']}' resulted in {experience['outcome']}. "\
                         f"Context: {experience['context']}. "\
                         f"Learning: {experience['learning']}"
                metadata = {
                    "category": "decision_outcomes",
                    "importance": 0.8,
                    "decision_id": experience.get("decision_id", ""),
                    "success": experience.get("success", True),
                    "trigger": "decision_outcome"
                }
            else:
                # Generic experience
                content = experience.get("description", "Unknown experience")
                metadata = {
                    "category": "general",
                    "importance": 0.5,
                    "trigger": "generic_experience"
                }
            
            # Add the memory
            memory_id = await self.add_memory(content, metadata)
            return bool(memory_id)
            
        except Exception as e:
            logger.error(f"❌ Error updating memory from experience: {e}")
            return False
    
    async def get_relevant_context(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant memory context for current situation"""
        try:
            context = {
                "survival_memories": [],
                "protocol_memories": [],
                "market_memories": [],
                "recent_decisions": []
            }
            
            # Query different types of memories based on situation
            if situation.get("treasury_level", 100) < 50:
                survival_memories = await self.query_memories(
                    query=f"treasury emergency survival low balance {situation.get('treasury_level', 0)}",
                    category="survival_critical",
                    limit=3
                )
                context["survival_memories"] = survival_memories
            
            if situation.get("market_condition"):
                market_memories = await self.query_memories(
                    query=f"market condition {situation['market_condition']} response strategy",
                    category="market_patterns",
                    limit=3
                )
                context["market_memories"] = market_memories
            
            if situation.get("protocol"):
                protocol_memories = await self.query_memories(
                    query=f"protocol {situation['protocol']} interaction experience",
                    category="protocol_behavior",
                    limit=3
                )
                context["protocol_memories"] = protocol_memories
            
            # Always get recent decision outcomes for learning
            recent_decisions = await self.query_memories(
                query="recent decision outcome success failure",
                category="decision_outcomes",
                limit=5
            )
            context["recent_decisions"] = recent_decisions
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Error getting relevant context: {e}")
            return {}
    
    async def consolidate_daily_memories(self) -> Dict[str, Any]:
        """Consolidate and summarize daily memories"""
        try:
            # Query all memories from the last 24 hours
            today_memories = self.memory.get_all(
                user_id=self.agent_id,
                limit=100  # Adjust based on expected daily volume
            )
            
            # Categorize and analyze
            memory_stats = {
                "total_memories": len(today_memories),
                "by_category": {},
                "high_importance": [],
                "patterns_identified": []
            }
            
            for memory in today_memories:
                metadata = memory.get("metadata", {})
                category = metadata.get("category", "unknown")
                importance = metadata.get("importance", 0)
                
                # Count by category
                if category not in memory_stats["by_category"]:
                    memory_stats["by_category"][category] = 0
                memory_stats["by_category"][category] += 1
                
                # Track high importance memories
                if importance >= 0.8:
                    memory_stats["high_importance"].append({
                        "content": memory.get("memory", ""),
                        "importance": importance,
                        "category": category
                    })
            
            # Create consolidation memory
            consolidation_content = (
                f"Daily memory consolidation: {memory_stats['total_memories']} memories formed. "
                f"Categories: {json.dumps(memory_stats['by_category'])}. "
                f"High importance events: {len(memory_stats['high_importance'])}"
            )
            
            await self.add_memory(
                content=consolidation_content,
                metadata={
                    "category": "daily_summary",
                    "importance": 0.7,
                    "stats": memory_stats,
                    "trigger": "daily_consolidation"
                }
            )
            
            return memory_stats
            
        except Exception as e:
            logger.error(f"❌ Error consolidating daily memories: {e}")
            return {}
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            all_memories = self.memory.get_all(user_id=self.agent_id, limit=1000)
            
            stats = {
                "total_memories": len(all_memories),
                "categories": {},
                "importance_distribution": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "oldest_memory": None,
                "newest_memory": None
            }
            
            for memory in all_memories:
                metadata = memory.get("metadata", {})
                category = metadata.get("category", "unknown")
                importance = metadata.get("importance", 0)
                
                # Category stats
                if category not in stats["categories"]:
                    stats["categories"][category] = 0
                stats["categories"][category] += 1
                
                # Importance distribution
                if importance >= 0.9:
                    stats["importance_distribution"]["critical"] += 1
                elif importance >= 0.7:
                    stats["importance_distribution"]["high"] += 1
                elif importance >= 0.4:
                    stats["importance_distribution"]["medium"] += 1
                else:
                    stats["importance_distribution"]["low"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting memory statistics: {e}")
            return {}