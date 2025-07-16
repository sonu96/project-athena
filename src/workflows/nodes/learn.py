"""
Learn Node - Form memories and extract patterns

This node consolidates experiences into long-term memory.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import hashlib

from langsmith import traceable

from ...core.consciousness import ConsciousnessState, Memory, Pattern
from ...memory.client import MemoryClient
from ...database.firestore_client import FirestoreClient

logger = logging.getLogger(__name__)


@traceable(name="learn_patterns")
async def learn_patterns(state: ConsciousnessState) -> ConsciousnessState:
    """
    Form memories and extract patterns from experiences
    
    This includes:
    - Storing important observations as memories
    - Identifying recurring patterns
    - Updating pattern confidence
    - Consolidating learning
    """
    logger.info(f"📚 Learning - {len(state.memory_formation_pending)} memories pending")
    
    try:
        memory_client = MemoryClient()
        firestore = FirestoreClient()
        
        # Form pending memories
        formed_memories = await _form_memories(state, memory_client)
        
        # Extract patterns from observations
        new_patterns = await _extract_patterns(state)
        
        # Update existing patterns
        await _update_patterns(state, new_patterns)
        
        # Consolidate learning
        learning_summary = await _consolidate_learning(state, formed_memories, firestore)
        
        # Clear pending memories
        state.memory_formation_pending = []
        
        # Update state with learning results
        state.market_data["learning_summary"] = learning_summary
        
        # Small cost for learning
        learning_cost = 0.0003 * len(formed_memories)  # Cost per memory
        state.update_treasury(state.treasury_balance - learning_cost, learning_cost)
        
        logger.info(
            f"✅ Learning complete - "
            f"Formed {len(formed_memories)} memories, "
            f"Found {len(new_patterns)} patterns"
        )
        
    except Exception as e:
        logger.error(f"❌ Error in learn node: {e}")
        state.errors.append(f"Learn error: {str(e)}")
    
    return state


async def _form_memories(
    state: ConsciousnessState, 
    memory_client: MemoryClient
) -> List[Memory]:
    """Form memories from pending list"""
    
    formed = []
    
    for content in state.memory_formation_pending:
        # Determine category
        category = _categorize_memory(content)
        
        # Calculate importance
        importance = _calculate_importance(content, state)
        
        # Skip if below threshold
        if importance < 0.3:
            continue
        
        # Create memory
        memory = Memory(
            id=_generate_memory_id(content),
            content=content,
            category=category,
            timestamp=datetime.utcnow(),
            importance=importance
        )
        
        # Store in Mem0
        try:
            await memory_client.add_memory(
                content=content,
                category=category,
                metadata={
                    "importance": importance,
                    "emotional_state": state.emotional_state.value,
                    "treasury_balance": state.treasury_balance,
                    "cycle_count": state.cycle_count
                }
            )
            
            # Add to state
            state.add_memory(memory)
            formed.append(memory)
            
            logger.debug(f"Formed memory: {category} - {content[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
    
    return formed


async def _extract_patterns(state: ConsciousnessState) -> List[Pattern]:
    """Extract patterns from current observations"""
    
    patterns = []
    
    # Pool volume patterns
    if len(state.observed_pools) >= 3:
        volume_pattern = _analyze_volume_patterns(state.observed_pools)
        if volume_pattern:
            patterns.append(volume_pattern)
    
    # Gas price patterns
    if state.gas_price_gwei is not None:
        gas_pattern = _analyze_gas_patterns(state)
        if gas_pattern:
            patterns.append(gas_pattern)
    
    # Yield patterns
    yield_pattern = _analyze_yield_patterns(state.observed_pools)
    if yield_pattern:
        patterns.append(yield_pattern)
    
    return patterns


async def _update_patterns(state: ConsciousnessState, new_patterns: List[Pattern]):
    """Update existing patterns with new observations"""
    
    for new_pattern in new_patterns:
        # Check if pattern already exists
        existing = None
        for pattern in state.active_patterns:
            if pattern.category == new_pattern.category and \
               _patterns_similar(pattern.description, new_pattern.description):
                existing = pattern
                break
        
        if existing:
            # Update existing pattern
            existing.occurrences += 1
            existing.last_seen = datetime.utcnow()
            existing.confidence = min(1.0, existing.confidence + 0.1)
            logger.debug(f"Updated pattern: {existing.description} (occurrences: {existing.occurrences})")
        else:
            # Add new pattern
            state.add_pattern(new_pattern)
            logger.info(f"New pattern discovered: {new_pattern.description}")


async def _consolidate_learning(
    state: ConsciousnessState,
    formed_memories: List[Memory],
    firestore: FirestoreClient
) -> Dict[str, Any]:
    """Consolidate learning into summary"""
    
    summary = {
        "cycle": state.cycle_count,
        "timestamp": datetime.utcnow(),
        "memories_formed": len(formed_memories),
        "active_patterns": len(state.active_patterns),
        "key_insights": []
    }
    
    # Add key insights
    if formed_memories:
        summary["key_insights"].append(f"Formed {len(formed_memories)} new memories")
    
    if state.active_patterns:
        confident_patterns = [p for p in state.active_patterns if p.confidence > 0.7]
        if confident_patterns:
            summary["key_insights"].append(
                f"High confidence in {len(confident_patterns)} patterns"
            )
    
    # Store learning summary
    try:
        await firestore.store_document(
            collection="learning_summaries",
            document_id=f"{state.agent_id}_{state.cycle_count}",
            data=summary
        )
    except Exception as e:
        logger.error(f"Failed to store learning summary: {e}")
    
    return summary


def _categorize_memory(content: str) -> str:
    """Categorize memory content"""
    
    content_lower = content.lower()
    
    if "[survival]" in content_lower:
        return "survival_memories"
    elif any(word in content_lower for word in ["gas", "gwei", "transaction"]):
        return "gas_patterns"
    elif any(word in content_lower for word in ["pattern", "trend", "correlation"]):
        return "market_patterns"
    elif any(word in content_lower for word in ["pool", "liquidity", "tvl"]):
        return "pool_behavior"
    elif any(word in content_lower for word in ["time", "hour", "day", "week"]):
        return "timing_patterns"
    elif any(word in content_lower for word in ["risk", "danger", "avoid", "safe"]):
        return "risk_patterns"
    else:
        return "general"


def _calculate_importance(content: str, state: ConsciousnessState) -> float:
    """Calculate memory importance"""
    
    importance = 0.5
    
    # Survival memories are always important
    if "[survival]" in content.lower():
        importance = 1.0
    
    # Boost for emotional intensity
    importance += state.emotional_intensity * 0.2
    
    # Boost for confident observations
    importance += (state.confidence_level - 0.5) * 0.3
    
    # Boost for financial relevance
    if str(state.treasury_balance) in content:
        importance += 0.1
    
    return min(1.0, max(0.0, importance))


def _generate_memory_id(content: str) -> str:
    """Generate unique ID for memory"""
    return hashlib.md5(f"{content}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]


def _analyze_volume_patterns(pools: List[PoolObservation]) -> Optional[Pattern]:
    """Analyze volume patterns across pools"""
    
    high_volume_ratios = [
        p for p in pools 
        if p.volume_24h_usd / p.tvl_usd > 0.2  # 20% daily volume
    ]
    
    if len(high_volume_ratios) >= 2:
        return Pattern(
            id=_generate_memory_id("volume_pattern"),
            description=f"High volume/TVL ratio observed in {len(high_volume_ratios)} pools",
            category="market_patterns",
            confidence=0.6,
            occurrences=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
    
    return None


def _analyze_gas_patterns(state: ConsciousnessState) -> Optional[Pattern]:
    """Analyze gas price patterns"""
    
    hour = datetime.utcnow().hour
    
    # Check for low gas windows
    if state.gas_price_gwei < 10 and hour in [2, 3, 4]:  # 2-4 AM UTC
        return Pattern(
            id=_generate_memory_id("gas_pattern"),
            description=f"Low gas ({state.gas_price_gwei} gwei) during early morning hours",
            category="gas_patterns",
            confidence=0.7,
            occurrences=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
    
    return None


def _analyze_yield_patterns(pools: List[PoolObservation]) -> Optional[Pattern]:
    """Analyze yield patterns"""
    
    high_yield_pools = [
        p for p in pools 
        if (p.fee_apy + p.reward_apy) > 0.3  # 30% APY
    ]
    
    if high_yield_pools:
        avg_yield = sum(p.fee_apy + p.reward_apy for p in high_yield_pools) / len(high_yield_pools)
        return Pattern(
            id=_generate_memory_id("yield_pattern"),
            description=f"Found {len(high_yield_pools)} high-yield pools averaging {avg_yield:.1%} APY",
            category="market_patterns",
            confidence=0.8,
            occurrences=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
    
    return None


def _patterns_similar(desc1: str, desc2: str) -> bool:
    """Check if two pattern descriptions are similar"""
    
    # Simple similarity check - could be enhanced
    words1 = set(desc1.lower().split())
    words2 = set(desc2.lower().split())
    
    overlap = len(words1.intersection(words2))
    total = len(words1.union(words2))
    
    return overlap / total > 0.6 if total > 0 else False