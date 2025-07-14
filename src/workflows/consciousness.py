"""
Consciousness state for the LangGraph nervous system

This module defines the unified state that flows through Athena's cognitive loop,
representing her complete mental state at any moment.
"""

from typing import TypedDict, List, Dict, Any
from datetime import datetime


class ConsciousnessState(TypedDict):
    """The complete state representing Athena's consciousness
    
    This state flows through the cognitive loop continuously, enabling
    the agent to perceive, think, feel, decide, and learn in a unified way.
    """
    
    # Core Identity
    agent_id: str
    emotional_state: str  # 'desperate', 'cautious', 'stable', 'confident'
    
    # Current Perception
    market_data: Dict[str, Any]
    treasury_balance: float
    days_until_bankruptcy: int
    
    # Active Context
    current_goal: str
    recent_memories: List[Dict]
    active_patterns: List[str]
    
    # Decision Context
    available_actions: List[str]
    last_decision: Dict[str, Any]
    decision_confidence: float
    
    # Learning Buffer
    current_experience: Dict[str, Any]
    lessons_learned: List[str]
    
    # Operational State
    cycle_count: int
    total_cost: float
    timestamp: datetime
    
    # Additional tracking
    errors: List[str]
    warnings: List[str]
    operational_mode: str  # 'survival_mode', 'conservative_mode', 'normal_mode', 'growth_mode'