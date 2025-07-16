"""
LLM Router - Dynamic model selection based on treasury and emotional state

Implements cost-aware model selection to ensure agent survival.
"""

import logging
from typing import Tuple, Dict, Any, Optional

from langchain_google_vertexai import ChatVertexAI
from langchain_core.language_models import BaseChatModel

from .state import ConsciousnessState
from ..core.emotions import EmotionalEngine, EmotionalState
from ..config import settings
from ..monitoring.cost_manager import cost_manager

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    Routes LLM requests to appropriate models based on:
    - Treasury balance (cost constraints)
    - Emotional state (urgency)
    - Task complexity
    """
    
    def __init__(self):
        self._models_cache: Dict[str, BaseChatModel] = {}
        self.emotional_engine = EmotionalEngine()
        
        # Initialize Vertex AI with project
        self.project_id = settings.gcp_project_id
        self.location = "us-central1"
        
        logger.info("✅ LLM Router initialized with Gemini models")
    
    def get_llm_for_state(
        self,
        state: ConsciousnessState,
        task_type: str = "general"
    ) -> Tuple[BaseChatModel, Dict[str, Any]]:
        """
        Get appropriate LLM based on current state
        
        Args:
            state: Current consciousness state
            task_type: Type of task (general, analysis, decision)
            
        Returns:
            Tuple of (model, config)
        """
        # Check if we're in shutdown mode
        if cost_manager.shutdown_triggered:
            logger.error("🛑 Cannot create LLM - Cost limit exceeded, services shut down")
            raise RuntimeError("Services shut down due to cost limit")
        
        # Get emotional state
        emotional_state = state.emotional_state
        
        # Adjust model based on emergency mode
        if cost_manager.emergency_mode:
            logger.warning("🚨 Emergency mode: Forcing cheapest model")
            emotional_state = EmotionalState.DESPERATE
        
        # Get model config
        model_config = EmotionalEngine.LLM_MODELS[emotional_state].copy()
        model_name = model_config["model"]
        
        # Create or get cached model
        if model_name not in self._models_cache:
            self._models_cache[model_name] = self._create_model(model_name, model_config)
        
        model = self._models_cache[model_name]
        
        logger.debug(
            f"Selected {model_name} for {emotional_state.value} state "
            f"(treasury: ${state.treasury_balance:.2f})"
        )
        
        return model, model_config
    
    def _create_model(self, model_name: str, config: Dict[str, Any]) -> BaseChatModel:
        """Create a Gemini model instance"""
        try:
            model = ChatVertexAI(
                model=model_name,
                project=self.project_id,
                location=self.location,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 1024),
                # Use default credentials from environment
            )
            
            logger.info(f"✅ Created Gemini model: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create model {model_name}: {e}")
            # Fallback to a mock model for testing
            return self._create_mock_model(model_name)
    
    def _create_mock_model(self, model_name: str) -> BaseChatModel:
        """Create a mock model for testing"""
        logger.warning(f"Using mock model for {model_name}")
        
        # Return a simple mock that returns canned responses
        class MockChatModel(BaseChatModel):
            def _generate(self, messages, **kwargs):
                return type('obj', (object,), {
                    'generations': [[type('obj', (object,), {
                        'text': f"Mock response from {model_name}",
                        'message': type('obj', (object,), {'content': f"Mock response from {model_name}"})()
                    })()]]
                })()
            
            def _llm_type(self):
                return "mock"
            
            async def _agenerate(self, messages, **kwargs):
                return self._generate(messages, **kwargs)
        
        return MockChatModel()
    
    def estimate_cost(
        self,
        state: ConsciousnessState,
        estimated_tokens: int = 1000
    ) -> float:
        """
        Estimate cost for a given number of tokens
        
        Args:
            state: Current consciousness state
            estimated_tokens: Estimated token count
            
        Returns:
            Estimated cost in USD
        """
        emotional_state = state.emotional_state
        config = EmotionalEngine.LLM_MODELS[emotional_state]
        cost_per_1k = config["cost_per_1k"]
        
        return (estimated_tokens / 1000) * cost_per_1k
    
    def get_model_info(self, state: ConsciousnessState) -> Dict[str, Any]:
        """Get information about the model that would be selected"""
        emotional_state = state.emotional_state
        config = EmotionalEngine.LLM_MODELS[emotional_state]
        
        return {
            "model": config["model"],
            "emotional_state": emotional_state.value,
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"],
            "cost_per_1k_tokens": config["cost_per_1k"],
            "estimated_hourly_cost": self.estimate_cost(state, 10000)  # 10k tokens/hour estimate
        }
    
    async def track_llm_cost(
        self,
        state: ConsciousnessState,
        input_tokens: int,
        output_tokens: int,
        operation: str = "llm_call"
    ) -> bool:
        """
        Track actual LLM usage cost
        
        Args:
            state: Current consciousness state
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens  
            operation: Description of the operation
            
        Returns:
            True if operation can continue, False if shutdown
        """
        total_tokens = input_tokens + output_tokens
        config = EmotionalEngine.LLM_MODELS[state.emotional_state]
        cost_per_1k = config["cost_per_1k"]
        
        # Calculate actual cost
        actual_cost = (total_tokens / 1000) * cost_per_1k
        
        # Track the cost
        can_continue = await cost_manager.add_cost(
            amount=actual_cost,
            service="gemini_api",
            operation=operation,
            metadata={
                "model": config["model"],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "emotional_state": state.emotional_state.value
            }
        )
        
        logger.info(
            f"💸 LLM Cost: ${actual_cost:.6f} "
            f"({total_tokens} tokens, {config['model']})"
        )
        
        return can_continue
    
    def can_afford_operation(self, state: ConsciousnessState, estimated_tokens: int = 1000) -> bool:
        """
        Check if we can afford an LLM operation
        
        Args:
            state: Current consciousness state
            estimated_tokens: Estimated token count
            
        Returns:
            True if we can afford the operation
        """
        if cost_manager.shutdown_triggered:
            return False
            
        estimated_cost = self.estimate_cost(state, estimated_tokens)
        return cost_manager.can_afford(estimated_cost)