"""
LLM Router - Dynamic model selection based on treasury and emotional state

Implements cost-aware model selection to ensure agent survival.
"""

import logging
from typing import Tuple, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from ..core.consciousness import ConsciousnessState
from ..core.emotions import EmotionalEngine, EmotionalState
from ..config import settings

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
        self._available_providers = self._detect_available_providers()
        
        if not self._available_providers:
            raise ValueError(
                "No LLM providers available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY"
            )
        
        logger.info(f"Available LLM providers: {list(self._available_providers.keys())}")
    
    def select_model(
        self, 
        state: ConsciousnessState,
        complexity: str = "medium"
    ) -> Tuple[BaseChatModel, Dict[str, Any]]:
        """
        Select appropriate model based on state and complexity
        
        Args:
            state: Current consciousness state
            complexity: Task complexity (low/medium/high)
            
        Returns:
            Tuple of (model, config)
        """
        
        # Get model preference from emotional state
        model_config = EmotionalEngine.get_llm_config(state.emotional_state)
        preferred_model = model_config["model"]
        
        # Override for extreme treasury situations
        if state.treasury_balance < 10:
            # Force cheapest model
            preferred_model = self._get_cheapest_model()
            model_config = self._get_model_config(preferred_model)
            logger.warning(f"💸 Low treasury - forcing {preferred_model}")
        
        # Check if preferred model is available
        available_model = self._find_available_model(preferred_model)
        
        if available_model != preferred_model:
            logger.info(f"Model {preferred_model} not available, using {available_model}")
            model_config = self._get_model_config(available_model)
        
        # Get or create model instance
        model = self._get_or_create_model(available_model)
        
        # Adjust config based on complexity
        if complexity == "low":
            model_config["max_tokens"] = min(256, model_config["max_tokens"])
            model_config["temperature"] = 0.3
        elif complexity == "high":
            model_config["max_tokens"] = min(2048, model_config["max_tokens"] * 2)
            model_config["temperature"] = min(0.9, model_config["temperature"] + 0.1)
        
        logger.debug(
            f"Selected model: {available_model} "
            f"(tokens: {model_config['max_tokens']}, temp: {model_config['temperature']})"
        )
        
        return model, model_config
    
    def _detect_available_providers(self) -> Dict[str, str]:
        """Detect which LLM providers have API keys"""
        
        available = {}
        
        # Check OpenAI
        if settings.openai_api_key:
            available["openai"] = settings.openai_api_key
            
        # Check Anthropic
        if settings.anthropic_api_key:
            available["anthropic"] = settings.anthropic_api_key
        
        return available
    
    def _get_cheapest_model(self) -> str:
        """Get the cheapest available model"""
        
        # Cheapest models by provider
        cheap_models = {
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-haiku-20240307"
        }
        
        # Return first available cheap model
        for provider in self._available_providers:
            if provider in cheap_models:
                return cheap_models[provider]
        
        # Fallback to any available
        return "gpt-3.5-turbo"
    
    def _find_available_model(self, preferred: str) -> str:
        """Find available model closest to preferred"""
        
        # Model mappings by provider
        model_providers = {
            "gpt-3.5-turbo": "openai",
            "gpt-4-turbo": "openai",
            "claude-3-haiku-20240307": "anthropic",
            "claude-3-sonnet-20240229": "anthropic",
            "claude-3-opus-20240229": "anthropic"
        }
        
        # Check if preferred model's provider is available
        preferred_provider = model_providers.get(preferred)
        if preferred_provider and preferred_provider in self._available_providers:
            return preferred
        
        # Map to equivalent model from available provider
        equivalents = {
            "claude-3-haiku-20240307": "gpt-3.5-turbo",
            "gpt-3.5-turbo": "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229": "gpt-4-turbo",
            "gpt-4-turbo": "claude-3-sonnet-20240229",
            "claude-3-opus-20240229": "gpt-4-turbo"
        }
        
        equivalent = equivalents.get(preferred, "gpt-3.5-turbo")
        equivalent_provider = model_providers.get(equivalent)
        
        if equivalent_provider and equivalent_provider in self._available_providers:
            return equivalent
        
        # Return any available model
        if "openai" in self._available_providers:
            return "gpt-3.5-turbo"
        elif "anthropic" in self._available_providers:
            return "claude-3-haiku-20240307"
        
        raise ValueError("No available models found")
    
    def _get_or_create_model(self, model_name: str) -> BaseChatModel:
        """Get cached model or create new instance"""
        
        if model_name in self._models_cache:
            return self._models_cache[model_name]
        
        # Create model based on provider
        if model_name.startswith("gpt"):
            model = ChatOpenAI(
                model=model_name,
                api_key=self._available_providers.get("openai")
            )
        elif model_name.startswith("claude"):
            model = ChatAnthropic(
                model=model_name,
                api_key=self._available_providers.get("anthropic")
            )
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        # Cache for reuse
        self._models_cache[model_name] = model
        return model
    
    def _get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        
        configs = {
            "gpt-3.5-turbo": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 512,
                "temperature": 0.5,
                "cost_per_1k": 0.0005
            },
            "gpt-4-turbo": {
                "model": "gpt-4-turbo",
                "max_tokens": 1024,
                "temperature": 0.7,
                "cost_per_1k": 0.01
            },
            "claude-3-haiku-20240307": {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 256,
                "temperature": 0.3,
                "cost_per_1k": 0.00025
            },
            "claude-3-sonnet-20240229": {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1024,
                "temperature": 0.7,
                "cost_per_1k": 0.003
            },
            "claude-3-opus-20240229": {
                "model": "claude-3-opus-20240229",
                "max_tokens": 2048,
                "temperature": 0.8,
                "cost_per_1k": 0.015
            }
        }
        
        return configs.get(model_name, configs["gpt-3.5-turbo"])