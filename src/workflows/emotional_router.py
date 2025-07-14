"""
Emotional routing logic for the nervous system

This module handles routing based on emotional state, automatically adjusting
operational parameters to ensure survival and optimal performance.
"""

from typing import Dict, Any, List

from .consciousness import ConsciousnessState


def emotional_router(state: ConsciousnessState) -> str:
    """Route execution based on emotional state
    
    This function determines the operational mode based on the agent's
    emotional state, which is derived from treasury balance and survival outlook.
    
    Args:
        state: Current consciousness state
        
    Returns:
        Operational mode string
    """
    
    emotional_state = state.get("emotional_state", "stable")
    
    if emotional_state == "desperate":
        # Minimal operations, maximum preservation
        return "survival_mode"
    elif emotional_state == "cautious":
        # Careful observation, reduced risk
        return "conservative_mode"
    elif emotional_state == "confident":
        # Active exploration, pattern seeking
        return "growth_mode"
    else:  # stable
        # Balanced operation
        return "normal_mode"


def get_operational_parameters(mode: str) -> Dict[str, Any]:
    """Get operational parameters based on mode
    
    Each mode has different parameters that affect:
    - Observation frequency (to save API costs)
    - Maximum daily spending
    - LLM model selection (cheaper vs better)
    - Memory importance threshold
    
    Args:
        mode: Operational mode from emotional_router
        
    Returns:
        Dictionary of operational parameters
    """
    
    parameters = {
        "survival_mode": {
            "observation_interval": 14400,  # 4 hours
            "max_daily_cost": 1.0,          # $1/day maximum
            "llm_model": "claude-3-haiku",  # Cheapest model
            "memory_threshold": 0.9,        # Only most critical memories
            "market_data_sources": ["minimal"],  # Reduce API calls
            "decision_frequency": "critical_only",
            "description": "Emergency preservation mode - minimal operations"
        },
        "conservative_mode": {
            "observation_interval": 7200,    # 2 hours
            "max_daily_cost": 5.0,          # $5/day maximum
            "llm_model": "claude-3-haiku",  # Still economical
            "memory_threshold": 0.7,        # Important memories
            "market_data_sources": ["basic"],
            "decision_frequency": "hourly",
            "description": "Conservative mode - careful resource usage"
        },
        "normal_mode": {
            "observation_interval": 3600,    # 1 hour
            "max_daily_cost": 10.0,         # $10/day maximum
            "llm_model": "claude-3-sonnet", # Better model
            "memory_threshold": 0.5,        # Balanced memory formation
            "market_data_sources": ["comprehensive"],
            "decision_frequency": "regular",
            "description": "Normal operations - balanced approach"
        },
        "growth_mode": {
            "observation_interval": 1800,    # 30 minutes
            "max_daily_cost": 20.0,         # $20/day maximum
            "llm_model": "claude-3-sonnet", # Best model
            "memory_threshold": 0.3,        # Learn from more experiences
            "market_data_sources": ["all"],
            "decision_frequency": "frequent",
            "description": "Growth mode - active learning and exploration"
        }
    }
    
    return parameters.get(mode, parameters["normal_mode"])


def get_decision_priorities(emotional_state: str) -> List[str]:
    """Get decision priorities based on emotional state
    
    Different emotional states prioritize different types of decisions.
    
    Args:
        emotional_state: Current emotional state
        
    Returns:
        List of priorities in order of importance
    """
    
    priorities = {
        "desperate": [
            "cost_reduction",
            "capital_preservation",
            "emergency_measures",
            "survival_critical"
        ],
        "cautious": [
            "risk_mitigation",
            "steady_observation",
            "capital_preservation",
            "conservative_growth"
        ],
        "stable": [
            "balanced_observation",
            "pattern_recognition",
            "strategic_positioning",
            "measured_growth"
        ],
        "confident": [
            "opportunity_identification",
            "active_learning",
            "strategic_expansion",
            "aggressive_growth"
        ]
    }
    
    return priorities.get(emotional_state, priorities["stable"])


def calculate_risk_tolerance(state: ConsciousnessState) -> float:
    """Calculate current risk tolerance based on state
    
    Risk tolerance is dynamically calculated based on:
    - Emotional state
    - Treasury balance
    - Days until bankruptcy
    - Recent performance
    
    Args:
        state: Current consciousness state
        
    Returns:
        Risk tolerance between 0.0 (minimum) and 1.0 (maximum)
    """
    
    # Base risk tolerance from emotional state
    emotional_risk_map = {
        "desperate": 0.1,
        "cautious": 0.3,
        "stable": 0.5,
        "confident": 0.8
    }
    
    base_risk = emotional_risk_map.get(state.get("emotional_state", "stable"), 0.5)
    
    # Adjust based on days until bankruptcy
    days_remaining = state.get("days_until_bankruptcy", 999)
    if days_remaining < 7:
        bankruptcy_multiplier = 0.2
    elif days_remaining < 30:
        bankruptcy_multiplier = 0.5
    elif days_remaining < 90:
        bankruptcy_multiplier = 0.8
    else:
        bankruptcy_multiplier = 1.0
    
    # Adjust based on recent decision success
    decision_confidence = state.get("decision_confidence", 0.5)
    confidence_adjustment = 0.2 * (decision_confidence - 0.5)  # +/- 0.1
    
    # Calculate final risk tolerance
    risk_tolerance = base_risk * bankruptcy_multiplier + confidence_adjustment
    
    # Clamp between 0.0 and 1.0
    return max(0.0, min(1.0, risk_tolerance))


def should_activate_emergency_mode(state: ConsciousnessState) -> bool:
    """Determine if emergency mode should be activated
    
    Emergency mode overrides normal operations when survival is at stake.
    
    Args:
        state: Current consciousness state
        
    Returns:
        True if emergency mode should be activated
    """
    
    # Check critical conditions
    balance = state.get("treasury_balance", 100.0)
    days_remaining = state.get("days_until_bankruptcy", 999)
    error_count = len(state.get("errors", []))
    
    # Activate emergency mode if any critical condition is met
    if balance < 10.0:  # Less than $10 remaining
        return True
    if days_remaining < 3:  # Less than 3 days until bankruptcy
        return True
    if error_count > 10:  # Too many errors
        return True
    
    return False