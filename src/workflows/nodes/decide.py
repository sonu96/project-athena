"""
Decide Node - Make decisions based on analysis and emotional state

In V1, decisions are limited to observations and memory formation.
In V2, this will include trading decisions.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

from langsmith import traceable

from ...core.consciousness import ConsciousnessState, Decision
from ...core.emotions import EmotionalEngine

logger = logging.getLogger(__name__)


@traceable(name="make_decision")
async def make_decision(state: ConsciousnessState) -> ConsciousnessState:
    """
    Make decisions based on current state
    
    V1 decisions include:
    - Which pools to observe more closely
    - What patterns to investigate
    - Which memories to form
    - When to adjust observation frequency
    """
    logger.info(f"🎯 Making decision - Confidence: {state.confidence_level:.1%}")
    
    try:
        # Get behavioral parameters
        behavior = EmotionalEngine.get_behavioral_params(state.emotional_state)
        
        # Make observation decisions
        observation_decisions = _decide_observations(state, behavior)
        
        # Make memory decisions
        memory_decisions = _decide_memories(state, behavior)
        
        # Make operational decisions
        operational_decisions = _decide_operations(state, behavior)
        
        # Combine all decisions
        all_decisions = observation_decisions + memory_decisions + operational_decisions
        
        # Record primary decision
        if all_decisions:
            primary_decision = all_decisions[0]
            state.record_decision(primary_decision)
            logger.info(f"📋 Primary decision: {primary_decision.decision_type} - {primary_decision.rationale}")
        else:
            # Default decision to continue observing
            default_decision = Decision(
                timestamp=datetime.utcnow(),
                decision_type="continue_observation",
                rationale="No actionable patterns identified, continuing observation",
                confidence=state.confidence_level,
                cost=0.0
            )
            state.record_decision(default_decision)
        
        # Update pending observations based on decisions
        state.pending_observations = [
            d.rationale for d in observation_decisions 
            if d.decision_type == "deep_observe"
        ]
        
        # Add memory formation candidates
        for decision in memory_decisions:
            if decision.decision_type == "form_memory":
                state.memory_formation_pending.append(decision.rationale)
        
        # Small cost for decision making
        decision_cost = 0.0002
        state.update_treasury(state.treasury_balance - decision_cost, decision_cost)
        
        logger.info(f"✅ Made {len(all_decisions)} decisions")
        
    except Exception as e:
        logger.error(f"❌ Error in decide node: {e}")
        state.errors.append(f"Decide error: {str(e)}")
    
    return state


def _decide_observations(state: ConsciousnessState, behavior: Dict[str, Any]) -> List[Decision]:
    """Decide what to observe more closely"""
    
    decisions = []
    
    # Check interesting patterns from analysis
    if state.market_data.get("analysis", {}).get("interesting_patterns"):
        patterns = state.market_data["analysis"]["interesting_patterns"]
        
        for pattern in patterns[:2]:  # Top 2 patterns
            # Only investigate if confidence is high enough
            if state.confidence_level >= 0.6:
                decision = Decision(
                    timestamp=datetime.utcnow(),
                    decision_type="deep_observe",
                    rationale=f"Investigate pattern: {pattern}",
                    confidence=state.confidence_level,
                    cost=0.0
                )
                decisions.append(decision)
    
    # Check high-yield pools
    for pool in state.observed_pools:
        total_apy = pool.fee_apy + pool.reward_apy
        
        # Interesting if APY is exceptional
        if total_apy > 0.5:  # 50% APY
            decision = Decision(
                timestamp=datetime.utcnow(),
                decision_type="track_pool",
                rationale=f"Track high-yield pool {pool.token0_symbol}/{pool.token1_symbol} with {total_apy:.1%} APY",
                confidence=0.8,
                cost=0.0
            )
            decisions.append(decision)
            break  # Only track one per cycle
    
    return decisions


def _decide_memories(state: ConsciousnessState, behavior: Dict[str, Any]) -> List[Decision]:
    """Decide what memories to form"""
    
    decisions = []
    memory_threshold = behavior["memory_threshold"]
    
    # Check memory candidates from analysis
    if state.market_data.get("analysis", {}).get("memory_candidates"):
        for candidate in state.market_data["analysis"]["memory_candidates"]:
            # Calculate importance
            importance = _calculate_memory_importance(candidate, state)
            
            if importance >= memory_threshold:
                decision = Decision(
                    timestamp=datetime.utcnow(),
                    decision_type="form_memory",
                    rationale=candidate,
                    confidence=importance,
                    cost=0.0
                )
                decisions.append(decision)
    
    # Check for pattern-based memories
    if state.active_patterns:
        for pattern in state.active_patterns:
            if pattern.confidence >= memory_threshold and pattern.occurrences >= 3:
                decision = Decision(
                    timestamp=datetime.utcnow(),
                    decision_type="form_memory",
                    rationale=f"Pattern confirmed: {pattern.description}",
                    confidence=pattern.confidence,
                    cost=0.0
                )
                decisions.append(decision)
                break  # One pattern memory per cycle
    
    return decisions


def _decide_operations(state: ConsciousnessState, behavior: Dict[str, Any]) -> List[Decision]:
    """Decide operational changes"""
    
    decisions = []
    
    # Decide on observation frequency adjustment
    current_freq = state.get_observation_frequency_minutes()
    target_freq = behavior["observation_frequency_hours"] * 60
    
    if abs(current_freq - target_freq) > 30:  # Significant difference
        decision = Decision(
            timestamp=datetime.utcnow(),
            decision_type="adjust_frequency",
            rationale=f"Adjust observation frequency from {current_freq}min to {target_freq}min based on {state.emotional_state.value} state",
            confidence=0.9,
            cost=0.0
        )
        decisions.append(decision)
    
    # Decide on resource conservation
    if EmotionalEngine.should_conserve_resources(state.emotional_state, state.emotional_intensity):
        decision = Decision(
            timestamp=datetime.utcnow(),
            decision_type="conserve_resources",
            rationale=f"Activate resource conservation - treasury at ${state.treasury_balance:.2f}",
            confidence=1.0,
            cost=0.0
        )
        decisions.append(decision)
    
    return decisions


def _calculate_memory_importance(candidate: str, state: ConsciousnessState) -> float:
    """Calculate importance score for a memory candidate"""
    
    importance = 0.5  # Base importance
    
    # Boost for financial relevance
    if any(word in candidate.lower() for word in ["profit", "loss", "yield", "apy", "risk"]):
        importance += 0.2
    
    # Boost for pattern recognition
    if any(word in candidate.lower() for word in ["pattern", "trend", "correlation", "signal"]):
        importance += 0.15
    
    # Boost for survival relevance
    if state.emotional_state in [EmotionalState.DESPERATE, EmotionalState.CAUTIOUS]:
        if any(word in candidate.lower() for word in ["safe", "risk", "danger", "avoid"]):
            importance += 0.25
    
    # Boost for high confidence
    importance *= state.confidence_level
    
    return min(1.0, importance)