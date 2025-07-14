"""
Enhanced Mem0 integration for personal DeFi agent
Provides structured memory storage and intelligent retrieval
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
from mem0 import Memory
from ..models import DecisionContext, DecisionResult, MemoryType


class EnhancedMem0Manager:
    """
    Enhanced memory manager that leverages Mem0's capabilities
    while maintaining compatibility with existing memory modules
    """
    
    def __init__(self, user_id: str = "personal"):
        self.memory = Memory()
        self.user_id = user_id
        
        # Import existing memory modules
        from .market_memory import MarketMemory
        from .protocol_memory import ProtocolMemory
        from .strategy_memory import StrategyMemory
        from .survival_memory import SurvivalMemory
        
        self.market_memory = MarketMemory()
        self.protocol_memory = ProtocolMemory()
        self.strategy_memory = StrategyMemory()
        self.survival_memory = SurvivalMemory()
        
        # Memory priorities for retention
        self.MEMORY_PRIORITIES = {
            "CRITICAL": 365,    # Keep for 1 year
            "IMPORTANT": 90,    # Keep for 90 days
            "ROUTINE": 30,      # Keep for 30 days
            "VERBOSE": 7        # Keep for 7 days
        }
    
    async def store_decision(self, decision: DecisionResult, context: DecisionContext) -> str:
        """Store a decision with rich context for future learning"""
        
        # Create comprehensive memory entry
        memory_content = {
            "timestamp": datetime.now().isoformat(),
            "decision": {
                "action": decision.action,
                "protocol": decision.protocol,
                "amount": decision.amount,
                "expected_yield": decision.expected_yield,
                "risk_score": decision.risk_score,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning
            },
            "context": {
                "treasury": context.current_treasury,
                "market": context.market_condition,
                "gas_price": context.gas_price,
                "available_protocols": context.available_protocols,
                "risk_tolerance": getattr(context, 'risk_tolerance', 0.5)
            },
            "blockchain_state": {
                "wallet_balance": decision.blockchain_balance if hasattr(decision, 'blockchain_balance') else None,
                "gas_estimate": None  # To be filled later
            },
            "outcome": "pending"  # Will be updated later
        }
        
        # Determine priority based on decision importance
        priority = self._calculate_priority(decision, context)
        
        # Store in Mem0 with searchable metadata
        memory_id = await self.memory.add(
            messages=[{
                "role": "assistant",
                "content": json.dumps(memory_content)
            }],
            user_id=self.user_id,
            metadata={
                "type": "decision",
                "action": decision.action,
                "protocol": decision.protocol or "none",
                "confidence": decision.confidence,
                "risk_score": decision.risk_score,
                "treasury_level": self._categorize_treasury(context.current_treasury),
                "market_condition": context.market_condition,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Also store in specialized memory modules for compatibility
        await self._sync_to_specialized_memories(memory_content)
        
        return memory_id
    
    async def get_successful_strategies(self, 
                                      market_condition: str,
                                      treasury_level: float,
                                      limit: int = 5) -> List[Dict[str, Any]]:
        """Find successful strategies in similar conditions"""
        
        treasury_category = self._categorize_treasury(treasury_level)
        
        # Search for similar successful decisions
        results = await self.memory.search(
            query=f"successful strategies when market was {market_condition} and treasury was {treasury_category}",
            user_id=self.user_id,
            limit=limit * 2  # Get more to filter
        )
        
        # Parse and filter results
        successful_strategies = []
        for result in results:
            try:
                memory = json.loads(result['memory'])
                
                # Only include successful outcomes
                if memory.get('outcome', {}).get('success', False):
                    # Calculate relevance score
                    relevance = self._calculate_relevance(memory, market_condition, treasury_level)
                    
                    successful_strategies.append({
                        'strategy': memory['decision'],
                        'context': memory['context'],
                        'outcome': memory['outcome'],
                        'relevance_score': relevance,
                        'timestamp': memory['timestamp']
                    })
            except:
                continue
        
        # Sort by relevance and return top results
        successful_strategies.sort(key=lambda x: x['relevance_score'], reverse=True)
        return successful_strategies[:limit]
    
    async def update_decision_outcome(self, 
                                    memory_id: str, 
                                    outcome: Dict[str, Any]) -> None:
        """Update a decision with its actual outcome"""
        
        # Get the original memory
        memory_data = await self.memory.get(memory_id)
        if not memory_data:
            return
        
        # Parse and update
        content = json.loads(memory_data['memory'])
        content['outcome'] = {
            'success': outcome.get('success', False),
            'actual_yield': outcome.get('actual_yield', 0),
            'gas_used': outcome.get('gas_used', 0),
            'profit_loss': outcome.get('profit_loss', 0),
            'completed_at': datetime.now().isoformat(),
            'notes': outcome.get('notes', '')
        }
        
        # Update in Mem0
        await self.memory.update(
            memory_id=memory_id,
            data=json.dumps(content)
        )
        
        # Learn from outcome
        await self._learn_from_outcome(content)
    
    async def get_risk_adjusted_strategies(self, 
                                         current_treasury: float) -> List[Dict[str, Any]]:
        """Get strategies appropriate for current treasury level"""
        
        risk_tolerance = self._calculate_risk_tolerance(current_treasury)
        
        # Search for strategies within risk tolerance
        results = await self.memory.search(
            query=f"strategies with risk score less than {risk_tolerance}",
            user_id=self.user_id,
            limit=10
        )
        
        strategies = []
        for result in results:
            try:
                memory = json.loads(result['memory'])
                if memory['decision']['risk_score'] <= risk_tolerance:
                    strategies.append(memory['decision'])
            except:
                continue
        
        return strategies
    
    async def get_memory_insights(self) -> Dict[str, Any]:
        """Get aggregated insights from all memories"""
        
        # Get all recent memories
        all_memories = await self.memory.get_all(
            user_id=self.user_id,
            limit=100
        )
        
        # Analyze patterns
        insights = {
            'total_decisions': len(all_memories),
            'success_rate': 0,
            'average_confidence': 0,
            'most_used_protocol': None,
            'best_performing_strategy': None,
            'risk_profile': {},
            'market_performance': {}
        }
        
        # Process memories for insights
        successes = 0
        total_confidence = 0
        protocol_counts = {}
        strategy_performance = {}
        
        for memory_entry in all_memories:
            try:
                memory = json.loads(memory_entry['memory'])
                
                # Success rate
                if memory.get('outcome', {}).get('success', False):
                    successes += 1
                
                # Confidence tracking
                total_confidence += memory['decision']['confidence']
                
                # Protocol usage
                protocol = memory['decision'].get('protocol', 'none')
                protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
                
                # Strategy performance
                action = memory['decision']['action']
                if action not in strategy_performance:
                    strategy_performance[action] = {'count': 0, 'successes': 0}
                
                strategy_performance[action]['count'] += 1
                if memory.get('outcome', {}).get('success', False):
                    strategy_performance[action]['successes'] += 1
                
            except:
                continue
        
        # Calculate insights
        if insights['total_decisions'] > 0:
            insights['success_rate'] = successes / insights['total_decisions']
            insights['average_confidence'] = total_confidence / insights['total_decisions']
        
        if protocol_counts:
            insights['most_used_protocol'] = max(protocol_counts, key=protocol_counts.get)
        
        # Find best performing strategy
        best_strategy = None
        best_success_rate = 0
        
        for strategy, stats in strategy_performance.items():
            if stats['count'] >= 3:  # Minimum sample size
                success_rate = stats['successes'] / stats['count']
                if success_rate > best_success_rate:
                    best_success_rate = success_rate
                    best_strategy = strategy
        
        insights['best_performing_strategy'] = {
            'name': best_strategy,
            'success_rate': best_success_rate
        }
        
        return insights
    
    async def cleanup_old_memories(self) -> int:
        """Remove old, low-priority memories to optimize storage"""
        
        cutoff_date = datetime.now() - timedelta(days=30)
        removed_count = 0
        
        # Get all memories
        all_memories = await self.memory.get_all(user_id=self.user_id)
        
        for memory_entry in all_memories:
            try:
                metadata = memory_entry.get('metadata', {})
                
                # Check if memory is old and low priority
                memory_date = datetime.fromisoformat(metadata.get('timestamp', ''))
                priority = metadata.get('priority', 'VERBOSE')
                
                retention_days = self.MEMORY_PRIORITIES.get(priority, 7)
                
                if memory_date < (datetime.now() - timedelta(days=retention_days)):
                    await self.memory.delete(memory_id=memory_entry['id'])
                    removed_count += 1
                    
            except:
                continue
        
        return removed_count
    
    # Helper methods
    
    def _calculate_priority(self, decision: DecisionResult, context: DecisionContext) -> str:
        """Calculate memory priority based on decision importance"""
        
        # Critical: High risk or low treasury
        if decision.risk_score > 0.7 or context.current_treasury < 100:
            return "CRITICAL"
        
        # Important: Medium risk or significant amount
        if decision.risk_score > 0.4 or (decision.amount and decision.amount > context.current_treasury * 0.3):
            return "IMPORTANT"
        
        # Routine: Normal operations
        if decision.confidence > 0.6:
            return "ROUTINE"
        
        # Verbose: Everything else
        return "VERBOSE"
    
    def _categorize_treasury(self, treasury: float) -> str:
        """Categorize treasury level for easier searching"""
        if treasury < 100:
            return "critical"
        elif treasury < 500:
            return "low"
        elif treasury < 1000:
            return "medium"
        else:
            return "high"
    
    def _calculate_risk_tolerance(self, treasury: float) -> float:
        """Calculate appropriate risk tolerance based on treasury"""
        if treasury < 100:
            return 0.2
        elif treasury < 500:
            return 0.4
        elif treasury < 1000:
            return 0.6
        else:
            return 0.8
    
    def _calculate_relevance(self, memory: Dict, market: str, treasury: float) -> float:
        """Calculate how relevant a past memory is to current situation"""
        
        relevance_score = 1.0
        
        # Market condition match
        if memory['context']['market'] == market:
            relevance_score *= 1.2
        
        # Treasury level similarity
        past_treasury = memory['context']['treasury']
        treasury_diff = abs(past_treasury - treasury) / max(past_treasury, treasury)
        relevance_score *= (1 - treasury_diff * 0.5)
        
        # Time decay (more recent = more relevant)
        memory_age = (datetime.now() - datetime.fromisoformat(memory['timestamp'])).days
        relevance_score *= max(0.5, 1 - (memory_age / 365))
        
        # Success bonus
        if memory.get('outcome', {}).get('success', False):
            relevance_score *= 1.3
        
        return relevance_score
    
    async def _sync_to_specialized_memories(self, memory_content: Dict) -> None:
        """Sync memory to specialized memory modules for compatibility"""
        
        decision = memory_content['decision']
        context = memory_content['context']
        
        # Sync to appropriate specialized memory
        if decision['action'] in ['HOLD', 'CONSERVATIVE_YIELD', 'AGGRESSIVE_YIELD']:
            await self.strategy_memory.store(memory_content)
        
        if context['treasury'] < 500:
            await self.survival_memory.store(memory_content)
        
        # Always sync market conditions
        await self.market_memory.store({
            'condition': context['market'],
            'timestamp': memory_content['timestamp'],
            'decision': decision['action']
        })
    
    async def _learn_from_outcome(self, completed_memory: Dict) -> None:
        """Learn from the outcome of a decision"""
        
        # Extract learning points
        success = completed_memory['outcome']['success']
        decision = completed_memory['decision']
        context = completed_memory['context']
        
        # Create a learning entry
        learning = {
            'lesson': f"{'Successful' if success else 'Failed'} {decision['action']} in {context['market']} market",
            'conditions': context,
            'outcome': completed_memory['outcome'],
            'recommendation': self._generate_recommendation(completed_memory)
        }
        
        # Store as a learning memory
        await self.memory.add(
            messages=[{
                "role": "assistant",
                "content": json.dumps(learning)
            }],
            user_id=self.user_id,
            metadata={
                "type": "learning",
                "success": success,
                "action": decision['action'],
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _generate_recommendation(self, memory: Dict) -> str:
        """Generate actionable recommendation from outcome"""
        
        success = memory['outcome']['success']
        decision = memory['decision']
        context = memory['context']
        
        if success:
            return f"Repeat {decision['action']} when market is {context['market']} and treasury is {context['treasury']}"
        else:
            return f"Avoid {decision['action']} in {context['market']} market conditions"