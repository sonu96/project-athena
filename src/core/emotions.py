"""
Emotional Intelligence System for Athena Agent

Emotions directly influence risk tolerance, decision making, and operational parameters.
"""

from enum import Enum
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EmotionalState(Enum):
    """
    Core emotional states that drive agent behavior
    """
    DESPERATE = "desperate"    # < 7 days runway - survival mode
    CAUTIOUS = "cautious"      # < 20 days - conservative
    STABLE = "stable"          # < 90 days - balanced
    CONFIDENT = "confident"    # > 90 days - growth mode


class EmotionalEngine:
    """
    Manages emotional state transitions and their effects on behavior
    """
    
    # State thresholds (days of runway)
    THRESHOLDS = {
        EmotionalState.DESPERATE: 7,
        EmotionalState.CAUTIOUS: 20,
        EmotionalState.STABLE: 90,
        EmotionalState.CONFIDENT: float('inf')
    }
    
    # LLM model selection by emotional state
    LLM_MODELS = {
        EmotionalState.DESPERATE: {
            "model": "gemini-2.0-flash-exp",
            "max_tokens": 256,
            "temperature": 0.3,
            "cost_per_1k": 0.0  # Free tier
        },
        EmotionalState.CAUTIOUS: {
            "model": "gemini-2.0-flash-exp",
            "max_tokens": 512,
            "temperature": 0.5,
            "cost_per_1k": 0.0  # Free tier
        },
        EmotionalState.STABLE: {
            "model": "gemini-1.5-pro",
            "max_tokens": 1024,
            "temperature": 0.7,
            "cost_per_1k": 0.00125  # $1.25 per 1M tokens
        },
        EmotionalState.CONFIDENT: {
            "model": "gemini-1.5-pro",
            "max_tokens": 2048,
            "temperature": 0.8,
            "cost_per_1k": 0.00125  # $1.25 per 1M tokens
        }
    }
    
    # Behavioral parameters by emotional state
    BEHAVIORS = {
        EmotionalState.DESPERATE: {
            "observation_frequency_hours": 4,
            "max_leverage": 1.0,  # No leverage in V2
            "memory_threshold": 0.3,  # Form memories more easily
            "pattern_sensitivity": 0.9,  # High sensitivity to patterns
            "risk_tolerance": 0.1,
            "focus": "survival"
        },
        EmotionalState.CAUTIOUS: {
            "observation_frequency_hours": 2,
            "max_leverage": 1.5,
            "memory_threshold": 0.5,
            "pattern_sensitivity": 0.7,
            "risk_tolerance": 0.3,
            "focus": "conservation"
        },
        EmotionalState.STABLE: {
            "observation_frequency_hours": 1,
            "max_leverage": 2.0,
            "memory_threshold": 0.6,
            "pattern_sensitivity": 0.5,
            "risk_tolerance": 0.5,
            "focus": "optimization"
        },
        EmotionalState.CONFIDENT: {
            "observation_frequency_hours": 0.5,
            "max_leverage": 3.0,
            "memory_threshold": 0.7,
            "pattern_sensitivity": 0.3,
            "risk_tolerance": 0.7,
            "focus": "growth"
        }
    }
    
    @classmethod
    def calculate_emotional_state(cls, days_until_bankruptcy: float) -> Tuple[EmotionalState, float]:
        """
        Calculate emotional state based on financial runway
        
        Returns:
            Tuple of (EmotionalState, intensity)
        """
        # Determine state
        if days_until_bankruptcy < cls.THRESHOLDS[EmotionalState.DESPERATE]:
            state = EmotionalState.DESPERATE
            # Intensity increases as bankruptcy approaches
            intensity = 1.0 - (days_until_bankruptcy / cls.THRESHOLDS[EmotionalState.DESPERATE])
            
        elif days_until_bankruptcy < cls.THRESHOLDS[EmotionalState.CAUTIOUS]:
            state = EmotionalState.CAUTIOUS
            # Intensity based on position within range
            range_size = cls.THRESHOLDS[EmotionalState.CAUTIOUS] - cls.THRESHOLDS[EmotionalState.DESPERATE]
            position = days_until_bankruptcy - cls.THRESHOLDS[EmotionalState.DESPERATE]
            intensity = 1.0 - (position / range_size)
            
        elif days_until_bankruptcy < cls.THRESHOLDS[EmotionalState.STABLE]:
            state = EmotionalState.STABLE
            # Intensity based on position within range
            range_size = cls.THRESHOLDS[EmotionalState.STABLE] - cls.THRESHOLDS[EmotionalState.CAUTIOUS]
            position = days_until_bankruptcy - cls.THRESHOLDS[EmotionalState.CAUTIOUS]
            intensity = 1.0 - (position / range_size)
            
        else:
            state = EmotionalState.CONFIDENT
            # Intensity decreases with more runway
            intensity = max(0.3, 1.0 - (days_until_bankruptcy - cls.THRESHOLDS[EmotionalState.STABLE]) / 100)
        
        # Clamp intensity between 0 and 1
        intensity = max(0.0, min(1.0, intensity))
        
        return state, intensity
    
    @classmethod
    def get_llm_config(cls, emotional_state: EmotionalState) -> Dict[str, Any]:
        """Get LLM configuration based on emotional state"""
        return cls.LLM_MODELS[emotional_state].copy()
    
    @classmethod
    def get_behavioral_params(cls, emotional_state: EmotionalState) -> Dict[str, Any]:
        """Get behavioral parameters based on emotional state"""
        return cls.BEHAVIORS[emotional_state].copy()
    
    @classmethod
    def should_conserve_resources(cls, emotional_state: EmotionalState, intensity: float) -> bool:
        """Determine if agent should conserve resources"""
        if emotional_state == EmotionalState.DESPERATE:
            return True
        elif emotional_state == EmotionalState.CAUTIOUS and intensity > 0.7:
            return True
        return False
    
    @classmethod
    def calculate_confidence_multiplier(cls, emotional_state: EmotionalState, base_confidence: float) -> float:
        """
        Calculate confidence multiplier based on emotional state
        
        Desperate agents are less confident, confident agents are more confident
        """
        multipliers = {
            EmotionalState.DESPERATE: 0.7,
            EmotionalState.CAUTIOUS: 0.85,
            EmotionalState.STABLE: 1.0,
            EmotionalState.CONFIDENT: 1.2
        }
        
        return base_confidence * multipliers[emotional_state]
    
    @classmethod
    def get_memory_importance_threshold(cls, emotional_state: EmotionalState) -> float:
        """
        Get minimum importance for memory formation
        
        Lower threshold = more memories formed
        """
        thresholds = {
            EmotionalState.DESPERATE: 0.3,  # Remember everything
            EmotionalState.CAUTIOUS: 0.5,
            EmotionalState.STABLE: 0.6,
            EmotionalState.CONFIDENT: 0.7   # Only important things
        }
        
        return thresholds[emotional_state]
    
    @classmethod
    def describe_state(cls, emotional_state: EmotionalState, intensity: float) -> str:
        """Generate human-readable description of emotional state"""
        
        intensity_words = {
            (0.0, 0.3): "slightly",
            (0.3, 0.6): "moderately", 
            (0.6, 0.8): "very",
            (0.8, 1.0): "extremely"
        }
        
        intensity_word = "moderately"
        for (low, high), word in intensity_words.items():
            if low <= intensity < high:
                intensity_word = word
                break
        
        descriptions = {
            EmotionalState.DESPERATE: f"{intensity_word} desperate - survival mode activated",
            EmotionalState.CAUTIOUS: f"{intensity_word} cautious - conserving resources",
            EmotionalState.STABLE: f"{intensity_word} stable - balanced operations",
            EmotionalState.CONFIDENT: f"{intensity_word} confident - growth oriented"
        }
        
        return descriptions[emotional_state]
    
    @classmethod
    def get_emoji(cls, emotional_state: EmotionalState) -> str:
        """Get emoji representation of emotional state"""
        emojis = {
            EmotionalState.DESPERATE: "😱",
            EmotionalState.CAUTIOUS: "😟",
            EmotionalState.STABLE: "😊",
            EmotionalState.CONFIDENT: "😎"
        }
        return emojis[emotional_state]