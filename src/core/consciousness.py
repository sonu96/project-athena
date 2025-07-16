"""
Enhanced Consciousness State for Athena Agent

This module defines the unified consciousness that flows through the cognitive loop.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

from .emotions import EmotionalState


class Decision(BaseModel):
    """Represents a decision made by the agent"""
    timestamp: datetime
    decision_type: str
    rationale: str
    confidence: float
    cost: float
    outcome: Optional[str] = None


class Memory(BaseModel):
    """Represents a memory stored by the agent"""
    id: str
    content: str
    category: str
    timestamp: datetime
    importance: float
    usage_count: int = 0
    last_accessed: Optional[datetime] = None


class Pattern(BaseModel):
    """Represents a recognized pattern"""
    id: str
    description: str
    category: str
    confidence: float
    occurrences: int
    first_seen: datetime
    last_seen: datetime


class PoolObservation(BaseModel):
    """Observation of an Aerodrome pool"""
    pool_address: str
    pool_type: str  # stable/volatile
    token0_symbol: str
    token1_symbol: str
    tvl_usd: float
    volume_24h_usd: float
    fee_apy: float
    reward_apy: float
    timestamp: datetime
    notes: Optional[str] = None


class ConsciousnessState(BaseModel):
    """
    The unified consciousness state that persists across the cognitive loop.
    This is the agent's complete mental model at any given moment.
    """
    
    # Identity
    agent_id: str = Field(..., description="Unique agent identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cycle_count: int = Field(default=0, description="Number of cognitive cycles completed")
    
    # Treasury & Survival
    treasury_balance: float = Field(..., description="Current balance in USD")
    daily_burn_rate: float = Field(default=0.0, description="Average daily cost")
    days_until_bankruptcy: float = Field(default=0.0, description="Runway in days")
    
    # Emotional Intelligence
    emotional_state: EmotionalState = Field(default=EmotionalState.STABLE)
    emotional_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_level: float = Field(default=0.5, ge=0.0, le=1.0)
    stress_level: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Market Observations
    market_data: Dict[str, Any] = Field(default_factory=dict)
    observed_pools: List[PoolObservation] = Field(default_factory=list)
    gas_price_gwei: Optional[float] = None
    
    # Memory System
    recent_memories: List[Memory] = Field(default_factory=list)
    active_patterns: List[Pattern] = Field(default_factory=list)
    memory_formation_pending: List[str] = Field(default_factory=list)
    
    # Decision Context
    last_decision: Optional[Decision] = None
    pending_observations: List[str] = Field(default_factory=list)
    decision_history: List[Decision] = Field(default_factory=list)
    
    # LLM Integration
    llm_model: str = Field(default="gpt-3.5-turbo", description="Current LLM model")
    total_llm_cost: float = Field(default=0.0, description="Total LLM costs")
    last_llm_call: Optional[datetime] = None
    
    # Operational State
    total_cost: float = Field(default=0.0, description="Total operational cost")
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Parallel Processing
    parallel_tasks: List[str] = Field(default_factory=list)
    task_results: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_treasury(self, new_balance: float, cost_incurred: float = 0.0):
        """Update treasury and financial metrics"""
        self.treasury_balance = new_balance
        self.total_cost += cost_incurred
        
        # Update burn rate (exponential moving average)
        if self.cycle_count > 0:
            alpha = 0.1  # Smoothing factor
            self.daily_burn_rate = (alpha * cost_incurred * 24) + ((1 - alpha) * self.daily_burn_rate)
        
        # Calculate runway
        if self.daily_burn_rate > 0:
            self.days_until_bankruptcy = self.treasury_balance / self.daily_burn_rate
        else:
            self.days_until_bankruptcy = float('inf')
    
    def add_memory(self, memory: Memory):
        """Add a new memory to recent memories"""
        self.recent_memories.append(memory)
        # Keep only last 100 memories in state
        if len(self.recent_memories) > 100:
            self.recent_memories = self.recent_memories[-100:]
    
    def add_pattern(self, pattern: Pattern):
        """Add or update a recognized pattern"""
        # Check if pattern already exists
        for i, p in enumerate(self.active_patterns):
            if p.id == pattern.id:
                # Update existing pattern
                self.active_patterns[i] = pattern
                return
        
        # Add new pattern
        self.active_patterns.append(pattern)
        # Keep only most confident patterns
        if len(self.active_patterns) > 50:
            self.active_patterns.sort(key=lambda p: p.confidence, reverse=True)
            self.active_patterns = self.active_patterns[:50]
    
    def record_decision(self, decision: Decision):
        """Record a decision made by the agent"""
        self.last_decision = decision
        self.decision_history.append(decision)
        # Keep only last 100 decisions
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
    
    def add_observation(self, pool_obs: PoolObservation):
        """Add a pool observation"""
        self.observed_pools.append(pool_obs)
        # Keep only last 50 observations
        if len(self.observed_pools) > 50:
            self.observed_pools = self.observed_pools[-50:]
    
    def increment_cycle(self):
        """Increment the cognitive cycle counter"""
        self.cycle_count += 1
        self.timestamp = datetime.utcnow()
    
    def calculate_stress(self) -> float:
        """Calculate current stress level based on multiple factors"""
        stress_factors = []
        
        # Financial stress
        if self.days_until_bankruptcy < 7:
            stress_factors.append(0.9)
        elif self.days_until_bankruptcy < 20:
            stress_factors.append(0.6)
        elif self.days_until_bankruptcy < 90:
            stress_factors.append(0.3)
        else:
            stress_factors.append(0.1)
        
        # Error stress
        recent_errors = len([e for e in self.errors if e])
        if recent_errors > 5:
            stress_factors.append(0.8)
        elif recent_errors > 2:
            stress_factors.append(0.4)
        
        # Decision stress
        if self.last_decision and self.last_decision.confidence < 0.5:
            stress_factors.append(0.5)
        
        # Calculate weighted average
        if stress_factors:
            self.stress_level = sum(stress_factors) / len(stress_factors)
        else:
            self.stress_level = 0.0
        
        return self.stress_level
    
    def should_form_survival_memory(self) -> bool:
        """Determine if current state warrants forming a survival memory"""
        return (
            self.emotional_state == EmotionalState.DESPERATE or
            self.days_until_bankruptcy < 3 or
            self.stress_level > 0.8 or
            len(self.errors) > 10
        )
    
    def get_observation_frequency_minutes(self) -> int:
        """Get observation frequency based on emotional state"""
        frequencies = {
            EmotionalState.DESPERATE: 240,    # 4 hours
            EmotionalState.CAUTIOUS: 120,     # 2 hours
            EmotionalState.STABLE: 60,        # 1 hour
            EmotionalState.CONFIDENT: 30      # 30 minutes
        }
        return frequencies.get(self.emotional_state, 60)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsciousnessState":
        """Create from dictionary"""
        # Handle enum conversion
        if 'emotional_state' in data and isinstance(data['emotional_state'], str):
            data['emotional_state'] = EmotionalState[data['emotional_state']]
        return cls(**data)