"""
Cost-aware LLM wrapper that tracks all API calls and enforces budget limits
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from .llm_router import LLMRouter
from .state import ConsciousnessState
from ..monitoring.cost_manager import cost_manager

logger = logging.getLogger(__name__)


class CostAwareLLM:
    """
    Wrapper for LLM calls that enforces cost limits and tracks usage
    """
    
    def __init__(self):
        self.router = LLMRouter()
        self.total_calls = 0
        
    async def generate_response(
        self,
        state: ConsciousnessState,
        messages: List[BaseMessage],
        task_type: str = "general",
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate LLM response with cost tracking
        
        Args:
            state: Current consciousness state
            messages: Chat messages
            task_type: Type of task
            max_tokens: Override max tokens
            
        Returns:
            Response text or None if shutdown
        """
        # Check if we can afford this operation
        estimated_tokens = self._estimate_tokens(messages, max_tokens)
        if not self.router.can_afford_operation(state, estimated_tokens):
            logger.error(
                f"🚫 Cannot afford LLM operation: "
                f"${self.router.estimate_cost(state, estimated_tokens):.6f} "
                f"(remaining: ${cost_manager.get_max_affordable_cost():.6f})"
            )
            return None
        
        try:
            # Get appropriate model
            model, config = self.router.get_llm_for_state(state, task_type)
            
            # Override max tokens if specified
            if max_tokens:
                config = config.copy()
                config["max_tokens"] = max_tokens
            
            logger.info(
                f"🤖 Making LLM call with {config['model']} "
                f"(estimated cost: ${self.router.estimate_cost(state, estimated_tokens):.6f})"
            )
            
            # Make the API call
            response = await model.ainvoke(messages, max_tokens=config.get("max_tokens"))
            
            # Extract actual token counts (if available)
            input_tokens = self._count_tokens(messages)
            output_tokens = self._count_tokens([AIMessage(content=response.content)])
            
            # Track the actual cost
            can_continue = await self.router.track_llm_cost(
                state=state,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                operation=f"{task_type}_llm_call"
            )
            
            self.total_calls += 1
            
            if not can_continue:
                logger.critical("🛑 LLM call succeeded but cost limit reached - shutting down")
                return response.content
            
            logger.debug(f"✅ LLM call successful ({input_tokens + output_tokens} tokens)")
            return response.content
            
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            # Don't track cost for failed calls
            return None
    
    def _estimate_tokens(self, messages: List[BaseMessage], max_tokens: Optional[int] = None) -> int:
        """Estimate token count for messages"""
        # Simple estimation: ~4 characters per token
        total_chars = sum(len(msg.content) for msg in messages)
        estimated_input = total_chars // 4
        estimated_output = max_tokens or 500  # Default estimate
        
        return estimated_input + estimated_output
    
    def _count_tokens(self, messages: List[BaseMessage]) -> int:
        """Count actual tokens (simple estimation)"""
        total_chars = sum(len(msg.content) for msg in messages)
        return max(1, total_chars // 4)  # Ensure at least 1 token
    
    def get_cost_status(self) -> Dict[str, Any]:
        """Get current cost status"""
        status = cost_manager.get_status()
        status["total_llm_calls"] = self.total_calls
        return status
    
    def get_budget_summary(self) -> str:
        """Get human-readable budget summary"""
        return cost_manager.get_cost_summary()


# Global instance
cost_aware_llm = CostAwareLLM()