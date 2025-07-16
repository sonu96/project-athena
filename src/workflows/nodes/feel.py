"""
Feel Node - Process emotions and update emotional state

Emotions directly influence behavior and risk tolerance.
"""

import logging
from datetime import datetime

from langsmith import traceable

from ...core.consciousness import ConsciousnessState
from ...core.emotions import EmotionalEngine, EmotionalState

logger = logging.getLogger(__name__)


@traceable(name="feel_emotions")
async def feel_emotions(state: ConsciousnessState) -> ConsciousnessState:
    """
    Process current situation and update emotional state
    
    Emotional state affects:
    - LLM model selection
    - Observation frequency
    - Memory formation threshold
    - Risk tolerance (V2)
    """
    logger.info(f"💭 Processing emotions - Current: {state.emotional_state.value}")
    
    try:
        # Calculate stress level
        stress = state.calculate_stress()
        
        # Determine new emotional state based on treasury
        new_state, intensity = EmotionalEngine.calculate_emotional_state(
            state.days_until_bankruptcy
        )
        
        # Check for state transition
        if new_state != state.emotional_state:
            logger.warning(f"🎭 Emotional transition: {state.emotional_state.value} → {new_state.value}")
            
            # Form memory of transition
            state.memory_formation_pending.append(
                f"Emotional state changed from {state.emotional_state.value} to {new_state.value} "
                f"at ${state.treasury_balance:.2f} balance"
            )
            
            # Special handling for desperate state
            if new_state == EmotionalState.DESPERATE:
                logger.critical("😱 ENTERING DESPERATE STATE - Survival mode activated!")
                state.memory_formation_pending.append(
                    f"[SURVIVAL] Entered desperate state with {state.days_until_bankruptcy:.1f} days runway"
                )
                state.warnings.append("Survival mode activated - conserving resources")
        
        # Update state
        state.emotional_state = new_state
        state.emotional_intensity = intensity
        state.stress_level = stress
        
        # Get behavioral parameters for new state
        behavior = EmotionalEngine.get_behavioral_params(new_state)
        
        # Log emotional status
        description = EmotionalEngine.describe_state(new_state, intensity)
        emoji = EmotionalEngine.get_emoji(new_state)
        
        logger.info(
            f"{emoji} Emotional state: {description} | "
            f"Stress: {stress:.1%} | Focus: {behavior['focus']}"
        )
        
        # Add emotional context to state
        state.market_data["emotional_context"] = {
            "state": new_state.value,
            "intensity": intensity,
            "stress": stress,
            "focus": behavior["focus"],
            "observation_frequency_hours": behavior["observation_frequency_hours"],
            "memory_threshold": behavior["memory_threshold"]
        }
        
        # Check if we should form survival memory
        if state.should_form_survival_memory():
            survival_context = _build_survival_context(state)
            state.memory_formation_pending.append(f"[SURVIVAL] {survival_context}")
            logger.warning(f"🚨 Survival memory flagged: {survival_context}")
        
        # Small cost for emotional processing
        emotional_cost = 0.0001
        state.update_treasury(state.treasury_balance - emotional_cost, emotional_cost)
        
    except Exception as e:
        logger.error(f"❌ Error in feel node: {e}")
        state.errors.append(f"Feel error: {str(e)}")
        # Keep current emotional state on error
    
    return state


def _build_survival_context(state: ConsciousnessState) -> str:
    """Build context for survival memory"""
    
    parts = []
    
    # Financial status
    parts.append(f"Balance: ${state.treasury_balance:.2f}")
    parts.append(f"Runway: {state.days_until_bankruptcy:.1f} days")
    parts.append(f"Burn rate: ${state.daily_burn_rate:.2f}/day")
    
    # Market context
    if state.observed_pools:
        top_pool = state.observed_pools[0]
        parts.append(f"Top pool: {top_pool.token0_symbol}/{top_pool.token1_symbol}")
        parts.append(f"APY: {top_pool.fee_apy + top_pool.reward_apy:.1%}")
    
    # Stress factors
    if state.errors:
        parts.append(f"Errors: {len(state.errors)}")
    
    # Timestamp
    parts.append(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    
    return " | ".join(parts)