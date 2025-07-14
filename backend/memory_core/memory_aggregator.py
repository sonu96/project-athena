"""
Memory aggregator that coordinates between Mem0 and specialized memory modules
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from .enhanced_mem0 import EnhancedMem0Manager
from .market_memory import MarketMemory
from .protocol_memory import ProtocolMemory
from .strategy_memory import StrategyMemory
from .survival_memory import SurvivalMemory


class MemoryAggregator:
    """
    Aggregates and coordinates all memory systems
    Provides unified interface for memory operations
    """
    
    def __init__(self, user_id: str = "personal"):
        # Initialize enhanced Mem0 manager
        self.mem0_manager = EnhancedMem0Manager(user_id)
        
        # Initialize specialized memories
        self.market = MarketMemory()
        self.protocol = ProtocolMemory()
        self.strategy = StrategyMemory()
        self.survival = SurvivalMemory()
        
        self.user_id = user_id
    
    async def store_comprehensive_memory(self, 
                                       decision_data: Dict,
                                       context_data: Dict,
                                       market_data: Optional[Dict] = None) -> str:
        """Store memory across all relevant systems"""
        
        # Store in Mem0 (primary storage)
        memory_id = await self.mem0_manager.store_decision(
            decision_data,
            context_data
        )
        
        # Store in specialized memories based on context
        tasks = []
        
        # Always store market conditions
        if market_data:
            tasks.append(
                self.market.store_market_condition(
                    condition=market_data.get('condition', 'unknown'),
                    indicators=market_data.get('indicators', {}),
                    timestamp=datetime.now()
                )
            )
        
        # Store strategy if action taken
        if decision_data.get('action') != 'HOLD':
            tasks.append(
                self.strategy.store_strategy_result(
                    strategy_name=decision_data['action'],
                    parameters=decision_data,
                    outcome={'pending': True},
                    context=context_data
                )
            )
        
        # Store survival memory if low treasury
        if context_data.get('current_treasury', 1000) < 500:
            tasks.append(
                self.survival.store_survival_event(
                    event_type='low_treasury_decision',
                    treasury_level=context_data['current_treasury'],
                    action_taken=decision_data['action'],
                    outcome={'pending': True}
                )
            )
        
        # Store protocol-specific data
        if decision_data.get('protocol'):
            tasks.append(
                self.protocol.store_protocol_experience(
                    protocol_name=decision_data['protocol'],
                    action_type=decision_data['action'],
                    parameters=decision_data,
                    outcome={'pending': True}
                )
            )
        
        # Execute all storage operations in parallel
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return memory_id
    
    async def get_relevant_memories(self,
                                  context: Dict,
                                  memory_types: List[str] = None) -> Dict[str, List[Dict]]:
        """Get all relevant memories for current context"""
        
        if memory_types is None:
            memory_types = ['strategies', 'market', 'survival', 'protocol']
        
        relevant_memories = {}
        
        # Get memories from Mem0 (primary source)
        if 'strategies' in memory_types:
            relevant_memories['strategies'] = await self.mem0_manager.get_successful_strategies(
                market_condition=context.get('market_condition', 'stable'),
                treasury_level=context.get('current_treasury', 1000),
                limit=5
            )
        
        # Get specialized memories
        if 'market' in memory_types:
            relevant_memories['market'] = await self.market.get_similar_conditions(
                current_condition=context.get('market_condition', 'stable'),
                limit=3
            )
        
        if 'survival' in memory_types and context.get('current_treasury', 1000) < 500:
            relevant_memories['survival'] = await self.survival.get_survival_strategies(
                treasury_level=context['current_treasury']
            )
        
        if 'protocol' in memory_types and context.get('protocol'):
            relevant_memories['protocol'] = await self.protocol.get_protocol_history(
                protocol_name=context['protocol'],
                limit=5
            )
        
        return relevant_memories
    
    async def get_decision_context(self, current_state: Dict) -> Dict[str, Any]:
        """Build comprehensive context using all memories"""
        
        # Get relevant memories
        memories = await self.get_relevant_memories(current_state)
        
        # Get insights from Mem0
        insights = await self.mem0_manager.get_memory_insights()
        
        # Build decision context
        context = {
            'current_state': current_state,
            'memory_insights': insights,
            'relevant_memories': memories,
            'recommendations': []
        }
        
        # Generate recommendations based on memories
        if memories.get('strategies'):
            for strategy in memories['strategies'][:3]:
                context['recommendations'].append({
                    'action': strategy['strategy']['action'],
                    'confidence': strategy['relevance_score'],
                    'reasoning': f"Similar success in {strategy['context']['market']} market"
                })
        
        # Add survival recommendations if needed
        if current_state.get('current_treasury', 1000) < 200:
            context['recommendations'].insert(0, {
                'action': 'HOLD',
                'confidence': 0.9,
                'reasoning': 'Treasury critically low - survival mode activated'
            })
        
        return context
    
    async def update_memory_outcomes(self, memory_id: str, outcome: Dict) -> None:
        """Update outcomes across all memory systems"""
        
        # Update in Mem0
        await self.mem0_manager.update_decision_outcome(memory_id, outcome)
        
        # Update in specialized memories based on outcome type
        if outcome.get('strategy_id'):
            await self.strategy.update_strategy_outcome(
                strategy_id=outcome['strategy_id'],
                actual_outcome=outcome
            )
        
        if outcome.get('protocol'):
            await self.protocol.update_protocol_metrics(
                protocol_name=outcome['protocol'],
                metrics=outcome
            )
    
    async def get_performance_summary(self, timeframe_days: int = 7) -> Dict[str, Any]:
        """Get aggregated performance summary from all memories"""
        
        # Get base insights from Mem0
        insights = await self.mem0_manager.get_memory_insights()
        
        # Get specialized summaries
        strategy_performance = await self.strategy.get_performance_summary(timeframe_days)
        market_accuracy = await self.market.get_prediction_accuracy(timeframe_days)
        survival_events = await self.survival.get_recent_events(timeframe_days)
        
        # Aggregate into comprehensive summary
        summary = {
            'overall': insights,
            'strategies': strategy_performance,
            'market_predictions': market_accuracy,
            'survival_events': survival_events,
            'health_score': self._calculate_health_score(insights, survival_events)
        }
        
        return summary
    
    async def optimize_memories(self) -> Dict[str, int]:
        """Optimize memory storage across all systems"""
        
        optimization_results = {}
        
        # Clean up old Mem0 memories
        optimization_results['mem0_cleaned'] = await self.mem0_manager.cleanup_old_memories()
        
        # Optimize specialized memories
        optimization_results['market_compressed'] = await self.market.compress_old_data()
        optimization_results['strategies_archived'] = await self.strategy.archive_old_strategies()
        
        return optimization_results
    
    def _calculate_health_score(self, insights: Dict, survival_events: List) -> float:
        """Calculate overall agent health score"""
        
        score = 0.5  # Base score
        
        # Success rate component (40%)
        score += insights.get('success_rate', 0.5) * 0.4
        
        # Confidence component (20%)
        avg_confidence = insights.get('average_confidence', 0.5)
        score += avg_confidence * 0.2
        
        # Survival component (40%)
        recent_survival_events = len([e for e in survival_events if e['severity'] == 'critical'])
        survival_score = max(0, 1 - (recent_survival_events * 0.2))
        score += survival_score * 0.4
        
        return min(1.0, max(0.0, score))