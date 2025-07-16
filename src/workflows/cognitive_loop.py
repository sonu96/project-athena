"""
Main Cognitive Loop - LangGraph workflow implementation

Implements the Sense → Think → Feel → Decide → Learn cycle.
"""

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langsmith import traceable

from .state import ConsciousnessState
from .cost_aware_llm import cost_aware_llm
from ..monitoring.cost_manager import cost_manager

logger = logging.getLogger(__name__)


async def sense_environment(state: ConsciousnessState) -> ConsciousnessState:
    """
    Sense node - Gather data from environment
    """
    if cost_manager.shutdown_triggered:
        logger.error("🛑 Sense operation blocked - cost limit exceeded")
        state.errors.append("Sense blocked: cost limit exceeded")
        return state
    
    logger.info("👁️  Sensing environment...")
    
    try:
        # Track sensing cost (minimal)
        await cost_manager.add_cost(0.001, "google_cloud", "sense_operation")
        
        # Update observations (this would normally fetch real data)
        state.pending_observations = ["market_data", "pool_states", "gas_prices"]
        state.cycle_count += 1
        
        logger.info(f"✅ Environment sensed (cycle {state.cycle_count})")
        
    except Exception as e:
        logger.error(f"❌ Sensing failed: {e}")
        state.errors.append(f"Sensing error: {e}")
    
    return state


async def think_analysis(state: ConsciousnessState) -> ConsciousnessState:
    """
    Think node - Analyze with LLM (cost-aware)
    """
    if cost_manager.shutdown_triggered:
        logger.error("🛑 Think operation blocked - cost limit exceeded")
        state.errors.append("Think blocked: cost limit exceeded")
        return state
    
    logger.info("🧠 Thinking and analyzing...")
    
    try:
        # Check if we can afford LLM operation
        from langchain_core.messages import HumanMessage
        
        # Create analysis prompt
        analysis_prompt = f"""
        Analyze the current situation:
        - Treasury: ${state.treasury_balance}
        - Emotional state: {state.emotional_state.value}
        - Cycle: {state.cycle_count}
        - Pending observations: {state.pending_observations}
        
        Provide a brief analysis in 1-2 sentences.
        """
        
        messages = [HumanMessage(content=analysis_prompt)]
        
        # Use cost-aware LLM
        response = await cost_aware_llm.generate_response(
            state=state,
            messages=messages,
            task_type="analysis"
        )
        
        if response:
            logger.info(f"🧠 Analysis: {response[:100]}...")
            # Store analysis result
            state.market_data = {"analysis": response}
        else:
            logger.warning("⚠️  LLM analysis blocked or failed")
            state.warnings.append("LLM analysis unavailable")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        state.errors.append(f"Analysis error: {e}")
    
    return state


async def feel_emotions(state: ConsciousnessState) -> ConsciousnessState:
    """
    Feel node - Process emotional state
    """
    if cost_manager.shutdown_triggered:
        logger.error("🛑 Feel operation blocked - cost limit exceeded")
        state.errors.append("Feel blocked: cost limit exceeded")
        return state
    
    logger.info("💭 Processing emotions...")
    
    try:
        from ..core.emotions import EmotionalEngine
        
        # Calculate days until bankruptcy
        days_until_bankruptcy = state.treasury_balance / 1.0  # $1/day burn rate
        
        # Update emotional state
        emotional_state, intensity = EmotionalEngine.calculate_emotional_state(days_until_bankruptcy)
        
        state.emotional_state = emotional_state
        state.emotional_intensity = intensity
        
        # Get behavioral parameters
        behavior = EmotionalEngine.get_behavioral_params(emotional_state)
        
        logger.info(
            f"😊 Emotional state: {EmotionalEngine.describe_state(emotional_state, intensity)} "
            f"{EmotionalEngine.get_emoji(emotional_state)}"
        )
        
        # Track minimal processing cost
        await cost_manager.add_cost(0.0001, "other", "emotion_processing")
        
    except Exception as e:
        logger.error(f"❌ Emotional processing failed: {e}")
        state.errors.append(f"Emotion error: {e}")
    
    return state


async def make_decision(state: ConsciousnessState) -> ConsciousnessState:
    """
    Decide node - Make decisions based on analysis
    """
    if cost_manager.shutdown_triggered:
        logger.error("🛑 Decision operation blocked - cost limit exceeded")
        state.errors.append("Decision blocked: cost limit exceeded")
        return state
    
    logger.info("🎯 Making decisions...")
    
    try:
        # Simple decision logic for V1 (observation mode)
        decision = {
            "action": "observe",
            "pools_to_monitor": ["USDC/ETH", "WETH/USDC"],
            "confidence": 0.8,
            "reasoning": "V1 observation mode - continue monitoring"
        }
        
        state.last_decision = decision
        
        logger.info(f"🎯 Decision: {decision['action']} (confidence: {decision['confidence']})")
        
        # Track decision cost
        await cost_manager.add_cost(0.0001, "other", "decision_making")
        
    except Exception as e:
        logger.error(f"❌ Decision making failed: {e}")
        state.errors.append(f"Decision error: {e}")
    
    return state


async def learn_patterns(state: ConsciousnessState) -> ConsciousnessState:
    """
    Learn node - Form memories and recognize patterns
    """
    if cost_manager.shutdown_triggered:
        logger.error("🛑 Learn operation blocked - cost limit exceeded")
        state.errors.append("Learn blocked: cost limit exceeded")
        return state
    
    logger.info("📚 Learning patterns...")
    
    try:
        # Check if we should form a memory
        if state.cycle_count % 5 == 0:  # Every 5th cycle
            from ..integrations.mem0_cloud import memory_client
            
            # Create memory content
            memory_content = f"""
            Cycle {state.cycle_count} Summary:
            - Emotional state: {state.emotional_state.value}
            - Treasury: ${state.treasury_balance}
            - Decision: {state.last_decision.get('action') if state.last_decision else 'none'}
            - Cost so far: ${cost_manager.get_status()['total_cost']:.4f}
            """
            
            # Store memory
            memory_id = await memory_client.store_memory(
                content=memory_content,
                category="cycle_summary",
                agent_id=state.agent_id
            )
            
            if memory_id:
                logger.info(f"💾 Memory formed: {memory_id}")
                # Track memory cost
                await cost_manager.add_cost(0.01, "mem0_api", "memory_formation")
            else:
                logger.warning("⚠️  Memory formation failed")
        
    except Exception as e:
        logger.error(f"❌ Learning failed: {e}")
        state.errors.append(f"Learning error: {e}")
    
    return state


def create_cognitive_workflow() -> StateGraph:
    """
    Create the main cognitive loop workflow with cost management
    
    Flow:
    1. Sense - Gather data from environment
    2. Think - Analyze with LLM (cost-aware)
    3. Feel - Process emotions
    4. Decide - Make decisions
    5. Learn - Form memories and patterns
    
    All nodes check cost limits and can be blocked if budget is exceeded.
    """
    
    # Create workflow with ConsciousnessState
    workflow = StateGraph(ConsciousnessState)
    
    # Add cost-aware nodes
    workflow.add_node("sense", sense_environment)
    workflow.add_node("think", think_analysis)
    workflow.add_node("feel", feel_emotions)
    workflow.add_node("decide", make_decision)
    workflow.add_node("learn", learn_patterns)
    
    # Define flow
    workflow.set_entry_point("sense")
    
    # Linear flow for V1 with cost protection
    workflow.add_edge("sense", "think")
    workflow.add_edge("think", "feel") 
    workflow.add_edge("feel", "decide")
    workflow.add_edge("decide", "learn")
    workflow.add_edge("learn", END)
    
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