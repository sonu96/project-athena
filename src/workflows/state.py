"""
State management for LangGraph workflows
"""

from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
from datetime import datetime

# Import ConsciousnessState for the nervous system
from .consciousness import ConsciousnessState


class AgentState(TypedDict):
    """Base state for all Athena workflows"""
    # Context
    timestamp: str
    agent_id: str
    workflow_type: str
    
    # Treasury & Emotional State
    treasury_balance: float
    daily_burn_rate: float
    days_until_bankruptcy: int
    emotional_state: str  # desperate, cautious, stable, confident
    risk_tolerance: float
    confidence_level: float
    
    # Market Data
    market_data: Dict[str, Any]
    market_condition: str  # bull, bear, volatile, neutral
    market_confidence: float
    
    # Memory Context
    relevant_memories: List[Dict[str, Any]]
    recent_decisions: List[Dict[str, Any]]
    patterns_detected: List[Dict[str, Any]]
    
    # Workflow Results
    llm_responses: Dict[str, Any]
    costs_incurred: List[Dict[str, Any]]
    errors: List[str]


class MarketAnalysisState(AgentState):
    """State for market analysis workflow"""
    # Market Analysis Specific
    data_sources: List[str]
    data_quality_scores: Dict[str, float]
    sentiment_analysis: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    protocol_yields: Dict[str, Any]
    
    # Analysis Results
    condition_classification: str
    confidence_score: float
    supporting_factors: List[str]
    risk_assessment: str
    recommended_actions: List[str]


class DecisionState(AgentState):
    """State for decision-making workflow"""
    # Decision Context
    decision_type: str
    available_options: List[str]
    decision_criteria: Dict[str, Any]
    
    # Memory Integration
    survival_memories: List[Dict[str, Any]]
    strategy_memories: List[Dict[str, Any]]
    protocol_memories: List[Dict[str, Any]]
    
    # Decision Process
    option_analysis: Dict[str, Any]
    risk_assessments: Dict[str, Any]
    cost_benefit_analysis: Dict[str, Any]
    
    # Final Decision
    chosen_option: str
    decision_reasoning: str
    decision_confidence: float
    expected_outcome: str


@dataclass
class WorkflowConfig:
    """Configuration for workflows"""
    max_llm_calls: int = 10
    timeout_seconds: int = 300
    retry_attempts: int = 3
    cost_limit_usd: float = 5.0
    
    # Model Selection
    default_model: str = "claude-3-haiku"
    critical_model: str = "claude-3-sonnet"
    complex_model: str = "gpt-4"
    
    # LangSmith
    enable_tracing: bool = True
    project_name: str = "athena-defi-phase1"


# Export all state types
__all__ = [
    'AgentState',
    'MarketAnalysisState', 
    'DecisionState',
    'ConsciousnessState',
    'WorkflowConfig'
]