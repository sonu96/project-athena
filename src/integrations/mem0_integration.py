"""
Mem0 integration for AI agent memory management
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging
import json
from mem0 import Memory

from ..config.settings import settings
from ..data.firestore_client import FirestoreClient
from ..data.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class Mem0Integration:
    """Manages AI agent memory using Mem0"""
    
    def __init__(self, firestore_client: FirestoreClient, bigquery_client: BigQueryClient):
        self.firestore = firestore_client
        self.bigquery = bigquery_client
        
        # Initialize Mem0
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "url": settings.vector_db_url,
                    "api_key": settings.mem0_api_key,
                }
            }
        }
        
        self.memory = Memory.from_config(config)
        self.agent_id = settings.agent_id
        
        # Memory categories for organization
        self.categories = {
            'survival': 'survival_critical',
            'protocol': 'protocol_behavior',
            'strategy': 'strategy_performance',
            'market': 'market_patterns',
            'decision': 'decision_outcomes'
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
            
            # Market behavior knowledge
            market_memories = [
                {
                    "content": "High volatility (>5% daily swings) often precedes major market moves. Increase observation frequency during volatile periods.",
                    "metadata": {
                        "category": "market_patterns",
                        "importance": 0.7,
                        "context": "volatility_response"
                    }
                },
                {
                    "content": "Gas prices above 100 gwei indicate network congestion. Delay non-urgent operations when gas is expensive.",
                    "metadata": {
                        "category": "market_patterns",
                        "importance": 0.6,
                        "context": "gas_optimization"
                    }
                }
            ]
            
            # Protocol knowledge
            protocol_memories = [
                {
                    "content": "Established protocols like Aave and Compound generally offer more stability but lower yields than newer protocols.",
                    "metadata": {
                        "category": "protocol_behavior",
                        "importance": 0.6,
                        "context": "protocol_selection"
                    }
                },
                {
                    "content": "Always check protocol TVL and audit status before considering interaction. Low TVL or unaudited protocols pose higher risks.",
                    "metadata": {
                        "category": "protocol_behavior",
                        "importance": 0.8,
                        "context": "risk_assessment"
                    }
                }
            ]
            
            # Store initial memories
            all_memories = survival_memories + market_memories + protocol_memories
            
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
            
            # Add memory to Mem0
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