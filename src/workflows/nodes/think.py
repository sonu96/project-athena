"""
Think Node - Analyze observations with LLM

Uses dynamic model selection based on treasury balance and emotional state.
"""

import logging
from typing import Dict, Any, List, Optional

from langsmith import traceable
from langchain_core.messages import HumanMessage, SystemMessage

from ...core.consciousness import ConsciousnessState
from ...core.emotions import EmotionalEngine
from ..llm_router import LLMRouter

logger = logging.getLogger(__name__)


@traceable(name="think_analysis")
async def think_analysis(state: ConsciousnessState) -> ConsciousnessState:
    """
    Analyze observations and market conditions using LLM
    
    Model selection is dynamic based on emotional state
    """
    logger.info(f"🧠 Thinking - Using {state.llm_model} model")
    
    try:
        # Get LLM configuration based on emotional state
        llm_router = LLMRouter()
        llm, model_config = llm_router.select_model(state)
        
        # Update state with selected model
        state.llm_model = model_config["model"]
        
        # Build analysis prompt
        prompt = _build_analysis_prompt(state)
        
        # Create messages
        messages = [
            SystemMessage(content=_get_system_prompt(state)),
            HumanMessage(content=prompt)
        ]
        
        # Invoke LLM with cost tracking
        response = await llm.ainvoke(
            messages,
            max_tokens=model_config["max_tokens"],
            temperature=model_config["temperature"]
        )
        
        # Parse analysis results
        analysis = _parse_analysis(response.content)
        
        # Update state with insights
        state.market_data["analysis"] = analysis
        state.confidence_level = analysis.get("confidence", 0.5)
        
        # Add pending observations for decision node
        if analysis.get("interesting_patterns"):
            state.pending_observations.extend(analysis["interesting_patterns"])
        
        # Calculate and track cost
        tokens_used = len(str(messages)) / 4 + len(response.content) / 4  # Rough estimate
        cost = (tokens_used / 1000) * model_config["cost_per_1k"]
        state.update_treasury(state.treasury_balance - cost, cost)
        state.total_llm_cost += cost
        
        logger.info(f"✅ Analysis complete - Confidence: {state.confidence_level:.1%}, Cost: ${cost:.4f}")
        
    except Exception as e:
        logger.error(f"❌ Error in think node: {e}")
        state.errors.append(f"Think error: {str(e)}")
        state.confidence_level = 0.3  # Low confidence on error
    
    return state


def _get_system_prompt(state: ConsciousnessState) -> str:
    """Get system prompt based on emotional state"""
    
    base_prompt = """You are Athena, an autonomous DeFi agent observing Aerodrome Finance pools.
Your role is to analyze market conditions and identify patterns for future trading.

Current emotional state: {emotional_state} - {emotional_description}
Treasury: ${treasury:.2f} (Days runway: {days_runway:.1f})

Your analysis should be:
- Focused on pattern recognition
- Cost-conscious given your financial state
- Appropriate to your emotional state
- Data-driven and objective
"""
    
    emotional_prompts = {
        "desperate": "\nYou are in SURVIVAL MODE. Be extremely conservative and only note critical observations.",
        "cautious": "\nYou are being CAUTIOUS. Focus on risk identification and safe opportunities.",
        "stable": "\nYou are STABLE. Provide balanced analysis of opportunities and risks.",
        "confident": "\nYou are CONFIDENT. Look for growth opportunities while maintaining discipline."
    }
    
    return base_prompt.format(
        emotional_state=state.emotional_state.value,
        emotional_description=EmotionalEngine.describe_state(state.emotional_state, state.emotional_intensity),
        treasury=state.treasury_balance,
        days_runway=state.days_until_bankruptcy
    ) + emotional_prompts.get(state.emotional_state.value, "")


def _build_analysis_prompt(state: ConsciousnessState) -> str:
    """Build analysis prompt from observations"""
    
    sections = []
    
    # Pool observations
    if state.observed_pools:
        pool_section = "POOL OBSERVATIONS:\n"
        for pool in state.observed_pools[:5]:  # Top 5 pools
            pool_section += f"- {pool.token0_symbol}/{pool.token1_symbol} ({pool.pool_type})\n"
            pool_section += f"  TVL: ${pool.tvl_usd:,.0f} | Volume 24h: ${pool.volume_24h_usd:,.0f}\n"
            pool_section += f"  APY: {pool.fee_apy:.1%} (fees) + {pool.reward_apy:.1%} (rewards) = {pool.fee_apy + pool.reward_apy:.1%}\n"
            pool_section += f"  {pool.notes}\n"
        sections.append(pool_section)
    
    # Market conditions
    if state.market_data:
        market_section = "MARKET CONDITIONS:\n"
        if "gas_price_gwei" in state.market_data:
            market_section += f"- Gas Price: {state.market_data['gas_price_gwei']} gwei (${state.market_data.get('gas_price_usd', 0):.2f})\n"
        sections.append(market_section)
    
    # Recent memories
    if state.recent_memories:
        memory_section = "RELEVANT MEMORIES:\n"
        for memory in state.recent_memories[:5]:
            memory_section += f"- {memory.content} (importance: {memory.importance:.1f})\n"
        sections.append(memory_section)
    
    # Analysis request
    sections.append("""
ANALYZE the above data and provide:
1. Key patterns or opportunities observed
2. Risk factors to consider
3. Confidence level (0-1) in your analysis
4. Any memories that should be formed

Respond in JSON format with keys: patterns, risks, confidence, memory_candidates
""")
    
    return "\n\n".join(sections)


def _parse_analysis(response: str) -> Dict[str, Any]:
    """Parse LLM analysis response"""
    
    # Try to parse as JSON
    try:
        import json
        # Find JSON in response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            analysis = json.loads(response[start:end])
            
            # Ensure required fields
            return {
                "patterns": analysis.get("patterns", []),
                "risks": analysis.get("risks", []),
                "confidence": float(analysis.get("confidence", 0.5)),
                "memory_candidates": analysis.get("memory_candidates", []),
                "interesting_patterns": analysis.get("patterns", [])[:3]  # Top 3 for further investigation
            }
    except Exception as e:
        logger.warning(f"Failed to parse JSON response: {e}")
    
    # Fallback to basic parsing
    return {
        "patterns": ["Market observation recorded"],
        "risks": ["Standard market risks"],
        "confidence": 0.5,
        "memory_candidates": [],
        "interesting_patterns": []
    }