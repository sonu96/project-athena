"""
Memory management system that coordinates experiences, learning, and recall
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging
import json

from ..integrations.mem0_integration import Mem0Integration
from ..data.firestore_client import FirestoreClient
from ..data.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class MemoryManager:
    """Orchestrates memory formation, retrieval, and learning"""
    
    def __init__(self, mem0_integration: Mem0Integration, 
                 firestore_client: FirestoreClient,
                 bigquery_client: BigQueryClient):
        self.mem0 = mem0_integration
        self.firestore = firestore_client
        self.bigquery = bigquery_client
        
        # Memory formation thresholds
        self.formation_criteria = {
            'treasury_change_threshold': 10.0,  # Form memory if treasury changes by >$10
            'emotional_state_change': True,     # Always form memory on emotional changes
            'market_volatility_threshold': 0.05, # 5% market swing triggers memory
            'decision_confidence_threshold': 0.8, # High confidence decisions remembered
            'failure_events': True              # Always remember failures
        }
        
        # Experience buffer for pattern detection
        self.experience_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 100
        
        # Learning metrics
        self.learning_stats = {
            'memories_formed': 0,
            'patterns_identified': 0,
            'successful_recalls': 0,
            'failed_recalls': 0
        }
    
    async def process_experience(self, experience: Dict[str, Any]) -> bool:
        """Process an experience and determine if it should form a memory"""
        try:
            # Add to buffer
            self.experience_buffer.append(experience)
            if len(self.experience_buffer) > self.max_buffer_size:
                self.experience_buffer.pop(0)
            
            # Determine if memory should be formed
            should_remember = await self._evaluate_experience_significance(experience)
            
            if should_remember:
                # Form memory through Mem0
                success = await self.mem0.update_memory_from_experience(experience)
                
                if success:
                    self.learning_stats['memories_formed'] += 1
                    
                    # Log memory formation event
                    await self.firestore.log_system_event(
                        "memory_formed",
                        {
                            "experience_type": experience.get("type"),
                            "significance": experience.get("significance", "medium"),
                            "total_memories": self.learning_stats['memories_formed']
                        }
                    )
                    
                    # Check for patterns
                    await self._detect_patterns()
                
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error processing experience: {e}")
            return False
    
    async def _evaluate_experience_significance(self, experience: Dict[str, Any]) -> bool:
        """Determine if an experience is significant enough to remember"""
        exp_type = experience.get("type", "")
        
        # Always remember certain types
        if exp_type in ["survival_event", "emotional_change", "critical_decision"]:
            return True
        
        # Check treasury changes
        if exp_type == "treasury_update":
            change = abs(experience.get("balance_change", 0))
            if change >= self.formation_criteria['treasury_change_threshold']:
                return True
        
        # Check market volatility
        if exp_type == "market_observation":
            volatility = experience.get("volatility", 0)
            if volatility >= self.formation_criteria['market_volatility_threshold']:
                return True
        
        # Check decision outcomes
        if exp_type == "decision_outcome":
            if experience.get("success") is False:  # Always remember failures
                return True
            confidence = experience.get("confidence", 0)
            if confidence >= self.formation_criteria['decision_confidence_threshold']:
                return True
        
        # Default: don't form memory for routine experiences
        return False
    
    async def get_relevant_memories(self, context: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Get memories relevant to current context"""
        try:
            # Build situation description
            situation = {
                "treasury_level": context.get("treasury", {}).get("balance", 100),
                "emotional_state": context.get("treasury", {}).get("emotional_state", "stable"),
                "market_condition": context.get("market", {}).get("condition", "unknown"),
                "current_task": context.get("task", "general"),
                "risk_level": context.get("risk_level", "medium")
            }
            
            # Get contextual memories from Mem0
            memory_context = await self.mem0.get_relevant_context(situation)
            
            # Track recall success
            total_memories = sum(len(memories) for memories in memory_context.values())
            if total_memories > 0:
                self.learning_stats['successful_recalls'] += 1
            else:
                self.learning_stats['failed_recalls'] += 1
            
            # Enhance with recent experiences
            memory_context['recent_experiences'] = self._get_recent_relevant_experiences(context)
            
            return memory_context
            
        except Exception as e:
            logger.error(f"❌ Error getting relevant memories: {e}")
            return {}
    
    async def _detect_patterns(self):
        """Detect patterns in recent experiences"""
        try:
            if len(self.experience_buffer) < 10:
                return
            
            # Look for repeated patterns
            patterns = {
                'repeated_failures': [],
                'successful_strategies': [],
                'cost_patterns': [],
                'market_responses': []
            }
            
            # Analyze recent experiences
            for i in range(len(self.experience_buffer) - 1):
                current = self.experience_buffer[i]
                next_exp = self.experience_buffer[i + 1]
                
                # Check for repeated failures
                if (current.get("type") == "decision_outcome" and 
                    current.get("success") is False and
                    next_exp.get("type") == "decision_outcome" and
                    next_exp.get("success") is False):
                    patterns['repeated_failures'].append({
                        'context': current.get("context"),
                        'decision': current.get("decision")
                    })
                
                # Check for successful strategies
                if (current.get("type") == "market_observation" and
                    next_exp.get("type") == "decision_outcome" and
                    next_exp.get("success") is True):
                    patterns['successful_strategies'].append({
                        'market_condition': current.get("condition"),
                        'action': next_exp.get("decision"),
                        'outcome': next_exp.get("outcome")
                    })
            
            # Form pattern memories if significant patterns found
            for pattern_type, pattern_list in patterns.items():
                if len(pattern_list) >= 3:  # Pattern repeated 3+ times
                    await self._create_pattern_memory(pattern_type, pattern_list)
                    self.learning_stats['patterns_identified'] += 1
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
    
    async def _create_pattern_memory(self, pattern_type: str, patterns: List[Dict]):
        """Create a memory from detected patterns"""
        try:
            if pattern_type == 'repeated_failures':
                content = f"Pattern detected: Repeated failures in {patterns[0].get('context', 'unknown context')}. " \
                         f"Avoid {patterns[0].get('decision', 'this approach')} in similar situations."
                category = "strategy_performance"
                importance = 0.9
                
            elif pattern_type == 'successful_strategies':
                content = f"Pattern detected: Successful strategy in {patterns[0].get('market_condition', 'market')} conditions. " \
                         f"Action '{patterns[0].get('action', 'unknown')}' consistently yields positive outcomes."
                category = "strategy_performance"
                importance = 0.8
                
            else:
                content = f"Pattern detected in {pattern_type}: {len(patterns)} occurrences"
                category = "general"
                importance = 0.6
            
            await self.mem0.add_memory(
                content=content,
                metadata={
                    "category": category,
                    "importance": importance,
                    "pattern_type": pattern_type,
                    "pattern_count": len(patterns),
                    "trigger": "pattern_detection"
                }
            )
            
            logger.info(f"📊 Pattern memory created: {pattern_type}")
            
        except Exception as e:
            logger.error(f"Error creating pattern memory: {e}")
    
    def _get_recent_relevant_experiences(self, context: Dict[str, Any]) -> List[Dict]:
        """Get recent experiences relevant to current context"""
        relevant = []
        current_task = context.get("task", "")
        
        for exp in self.experience_buffer[-10:]:  # Last 10 experiences
            # Check relevance
            if (exp.get("type") == current_task or
                exp.get("market_condition") == context.get("market", {}).get("condition") or
                exp.get("emotional_state") == context.get("treasury", {}).get("emotional_state")):
                relevant.append({
                    "type": exp.get("type"),
                    "outcome": exp.get("outcome", "unknown"),
                    "lesson": exp.get("lesson", ""),
                    "timestamp": exp.get("timestamp", "")
                })
        
        return relevant
    
    async def consolidate_learning(self) -> Dict[str, Any]:
        """Consolidate daily learning into insights"""
        try:
            # Get memory statistics
            memory_stats = await self.mem0.get_memory_statistics()
            
            # Analyze experience buffer
            experience_summary = {
                'total_experiences': len(self.experience_buffer),
                'experience_types': {},
                'success_rate': 0,
                'common_contexts': []
            }
            
            successes = 0
            total_decisions = 0
            
            for exp in self.experience_buffer:
                exp_type = exp.get("type", "unknown")
                experience_summary['experience_types'][exp_type] = \
                    experience_summary['experience_types'].get(exp_type, 0) + 1
                
                if exp_type == "decision_outcome":
                    total_decisions += 1
                    if exp.get("success", False):
                        successes += 1
            
            if total_decisions > 0:
                experience_summary['success_rate'] = successes / total_decisions
            
            # Create consolidation summary
            consolidation = {
                'date': datetime.now(timezone.utc).date().isoformat(),
                'memory_stats': memory_stats,
                'experience_summary': experience_summary,
                'learning_metrics': self.learning_stats,
                'key_insights': await self._extract_key_insights()
            }
            
            # Store consolidation
            await self.firestore.log_system_event(
                "daily_learning_consolidation",
                consolidation
            )
            
            # Create daily summary memory
            await self.mem0.consolidate_daily_memories()
            
            return consolidation
            
        except Exception as e:
            logger.error(f"❌ Error consolidating learning: {e}")
            return {}
    
    async def _extract_key_insights(self) -> List[str]:
        """Extract key insights from recent experiences"""
        insights = []
        
        # Analyze patterns in experience buffer
        if self.experience_buffer:
            # Check for improving performance
            recent_success_rate = sum(
                1 for exp in self.experience_buffer[-20:]
                if exp.get("type") == "decision_outcome" and exp.get("success", False)
            ) / min(20, len(self.experience_buffer))
            
            if recent_success_rate > 0.7:
                insights.append("Decision success rate improving - current strategies working well")
            elif recent_success_rate < 0.3:
                insights.append("Low decision success rate - need to adjust strategies")
            
            # Check for cost efficiency
            recent_costs = [
                exp.get("cost", 0) for exp in self.experience_buffer[-10:]
                if "cost" in exp
            ]
            if recent_costs and sum(recent_costs) / len(recent_costs) < 5.0:
                insights.append("Cost efficiency improving - maintaining low operational costs")
        
        return insights
    
    async def query_learning_history(self, query: str, days: int = 7) -> Dict[str, Any]:
        """Query historical learning data"""
        try:
            # Query memories
            historical_memories = await self.mem0.query_memories(
                query=query,
                limit=20
            )
            
            # Get pattern data from BigQuery
            patterns = await self.bigquery.get_market_patterns(days=days)
            
            # Combine into learning history
            history = {
                'query': query,
                'period_days': days,
                'relevant_memories': historical_memories,
                'market_patterns': patterns,
                'learning_progression': self._calculate_learning_progression()
            }
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Error querying learning history: {e}")
            return {}
    
    def _calculate_learning_progression(self) -> Dict[str, float]:
        """Calculate metrics showing learning progression"""
        if self.learning_stats['memories_formed'] == 0:
            return {'progression_score': 0}
        
        # Calculate various progression metrics
        recall_accuracy = (
            self.learning_stats['successful_recalls'] / 
            max(1, self.learning_stats['successful_recalls'] + self.learning_stats['failed_recalls'])
        )
        
        memory_quality = self.learning_stats['patterns_identified'] / max(1, self.learning_stats['memories_formed'])
        
        return {
            'progression_score': (recall_accuracy + memory_quality) / 2,
            'recall_accuracy': recall_accuracy,
            'memory_quality': memory_quality,
            'total_memories': self.learning_stats['memories_formed'],
            'patterns_found': self.learning_stats['patterns_identified']
        }