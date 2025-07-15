"""
LLM Factory - Manages LLM selection based on cost and performance needs
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

from .gemini_integration import GeminiIntegration, GEMINI_PROMPTS
from ..config.settings import settings

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers"""
    GEMINI_FLASH = "gemini-flash-2.0"  # Ultra cheap - $0.075/$0.30 per 1M tokens
    CLAUDE_HAIKU = "claude-3-haiku"     # Fast - $0.25/$1.25 per 1M tokens  
    GPT4_MINI = "gpt-4-mini"            # Balanced - $0.15/$0.60 per 1M tokens


class LLMFactory:
    """Factory for creating appropriate LLM instances based on context"""
    
    def __init__(self):
        # Initialize providers
        self.providers = {
            LLMProvider.GEMINI_FLASH: GeminiIntegration()
        }
        
        # Default to cheapest option
        self.default_provider = LLMProvider.GEMINI_FLASH
        
        # Cost thresholds for provider selection
        self.cost_thresholds = {
            "critical": 0.001,  # Use only Gemini when desperate
            "low": 0.01,       # Prefer Gemini
            "normal": 0.05,     # Can use any provider
            "high": 0.10       # Can use premium models
        }
        
        logger.info("✅ LLM Factory initialized with Gemini Flash 2.0 as primary")
    
    async def create(self, 
                    prompt: str,
                    emotional_state: str = "stable",
                    max_cost: float = 0.01,
                    require_streaming: bool = False) -> Dict[str, Any]:
        """
        Create LLM response based on context and cost constraints
        
        Args:
            prompt: The prompt to send
            emotional_state: Current emotional state of agent
            max_cost: Maximum cost allowed for this request
            require_streaming: Whether streaming is required
            
        Returns:
            Response dict with content and metadata
        """
        try:
            # Select provider based on cost constraints
            provider = self._select_provider(emotional_state, max_cost)
            
            # Get appropriate system prompt
            system_prompt = GEMINI_PROMPTS.get(emotional_state, GEMINI_PROMPTS["stable"])
            
            # For V1, we only use Gemini
            if provider == LLMProvider.GEMINI_FLASH:
                gemini = self.providers[provider]
                
                # Adjust token limits based on emotional state
                max_tokens = {
                    "desperate": 256,   # Minimal responses
                    "cautious": 384,    # Short responses
                    "stable": 512,      # Normal responses
                    "confident": 768    # Detailed responses
                }.get(emotional_state, 512)
                
                response = await gemini.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=0.1 if emotional_state == "desperate" else 0.3
                )
                
                # Add provider info
                response["provider"] = provider.value
                response["emotional_state"] = emotional_state
                
                return response
            
            else:
                # Fallback for other providers (not implemented in V1)
                logger.warning(f"Provider {provider} not implemented, using Gemini")
                return await self.create(prompt, emotional_state, max_cost, require_streaming)
                
        except Exception as e:
            logger.error(f"❌ LLM Factory error: {e}")
            return {
                "content": "",
                "error": str(e),
                "provider": "none",
                "cost": {"total": 0}
            }
    
    def _select_provider(self, emotional_state: str, max_cost: float) -> LLMProvider:
        """Select appropriate provider based on state and cost"""
        
        # In desperate mode, always use cheapest
        if emotional_state == "desperate":
            return LLMProvider.GEMINI_FLASH
        
        # In cautious mode, prefer cheap options
        if emotional_state == "cautious" and max_cost < self.cost_thresholds["low"]:
            return LLMProvider.GEMINI_FLASH
        
        # For V1, always use Gemini Flash
        return LLMProvider.GEMINI_FLASH
    
    async def estimate_cost(self, prompt: str, provider: LLMProvider = None) -> float:
        """Estimate cost for a prompt"""
        if provider is None:
            provider = self.default_provider
        
        if provider == LLMProvider.GEMINI_FLASH:
            gemini = self.providers[provider]
            return gemini.estimate_cost(prompt, is_input=True)
        
        return 0.0
    
    async def get_daily_usage(self) -> Dict[str, Any]:
        """Get daily usage across all providers"""
        usage = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "by_provider": {}
        }
        
        # Get Gemini usage
        gemini = self.providers[LLMProvider.GEMINI_FLASH]
        gemini_usage = await gemini.check_daily_usage()
        
        usage["by_provider"]["gemini"] = gemini_usage
        usage["total_cost"] += gemini_usage.get("cost_usd", 0)
        usage["total_tokens"] += gemini_usage.get("tokens_used", 0)
        
        return usage


# Global factory instance
llm_factory = LLMFactory()


async def get_llm_response(prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to get LLM response with context
    
    Args:
        prompt: The prompt
        context: Context dict with emotional_state, treasury_balance, etc
        
    Returns:
        LLM response
    """
    emotional_state = context.get("emotional_state", "stable")
    treasury_balance = context.get("treasury_balance", 100.0)
    
    # Calculate max cost based on treasury
    if treasury_balance < 10:
        max_cost = 0.001  # Extreme conservation
    elif treasury_balance < 30:
        max_cost = 0.01   # Conservative
    elif treasury_balance < 100:
        max_cost = 0.05   # Normal
    else:
        max_cost = 0.10   # Can afford better models
    
    return await llm_factory.create(
        prompt=prompt,
        emotional_state=emotional_state,
        max_cost=max_cost
    )