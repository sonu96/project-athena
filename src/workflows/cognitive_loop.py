"""
Main Cognitive Loop - LangGraph workflow implementation

Implements the Sense → Think → Feel → Decide → Learn cycle.
"""

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langsmith import traceable

from ..core.consciousness import ConsciousnessState
from .nodes import (
    sense_environment,
    think_analysis,
    feel_emotions,
    make_decision,
    learn_patterns
)

logger = logging.getLogger(__name__)


def create_cognitive_workflow() -> StateGraph:
    """
    Create the main cognitive loop workflow
    
    Flow:
    1. Sense - Gather data from environment
    2. Think - Analyze with LLM
    3. Feel - Process emotions
    4. Decide - Make decisions
    5. Learn - Form memories and patterns
    """
    
    # Create workflow with ConsciousnessState
    workflow = StateGraph(ConsciousnessState)
    
    # Add nodes
    workflow.add_node("sense", sense_environment)
    workflow.add_node("think", think_analysis)
    workflow.add_node("feel", feel_emotions)
    workflow.add_node("decide", make_decision)
    workflow.add_node("learn", learn_patterns)
    
    # Define flow
    workflow.set_entry_point("sense")
    
    # Linear flow for V1
    workflow.add_edge("sense", "think")
    workflow.add_edge("think", "feel")
    workflow.add_edge("feel", "decide")
    workflow.add_edge("decide", "learn")
    workflow.add_edge("learn", END)
    
    # Compile workflow
    return workflow.compile()


@traceable(name="cognitive_cycle")
async def run_cognitive_cycle(
    workflow: StateGraph,
    initial_state: ConsciousnessState
) -> ConsciousnessState:
    """
    Run a single cognitive cycle
    
    Args:
        workflow: Compiled LangGraph workflow
        initial_state: Current consciousness state
        
    Returns:
        Updated consciousness state
    """
    
    try:
        # Increment cycle counter
        initial_state.increment_cycle()
        
        logger.info(
            f"🔄 Starting cognitive cycle #{initial_state.cycle_count} "
            f"[{initial_state.emotional_state.value}]"
        )
        
        # Run workflow
        result = await workflow.ainvoke(initial_state)
        
        # Extract final state
        if isinstance(result, ConsciousnessState):
            final_state = result
        else:
            # Handle different return formats
            final_state = result.get("__end__", initial_state)
        
        # Log cycle summary
        logger.info(
            f"✅ Cycle #{final_state.cycle_count} complete - "
            f"Cost: ${final_state.total_cost - initial_state.total_cost:.4f} | "
            f"Memories: {len(final_state.memory_formation_pending)} formed | "
            f"Patterns: {len(final_state.active_patterns)} active"
        )
        
        return final_state
        
    except Exception as e:
        logger.error(f"❌ Error in cognitive cycle: {e}", exc_info=True)
        initial_state.errors.append(f"Cycle error: {str(e)}")
        return initial_state


def should_run_cycle(state: ConsciousnessState) -> bool:
    """
    Determine if a new cognitive cycle should run
    
    Based on:
    - Time since last cycle
    - Emotional state (observation frequency)
    - Resource availability
    """
    
    # Check if in survival mode
    if state.emotional_state == EmotionalState.DESPERATE:
        # Only essential cycles in desperate state
        if state.cycle_count % 10 != 0:  # Every 10th cycle
            logger.debug("Skipping cycle - conserving resources in desperate state")
            return False
    
    # Check treasury
    if state.treasury_balance < 1.0:
        logger.warning("Treasury below $1 - halting operations")
        return False
    
    # Check error rate
    recent_errors = len([e for e in state.errors[-10:] if e])
    if recent_errors > 5:
        logger.warning(f"High error rate ({recent_errors}/10) - pausing operations")
        return False
    
    return True