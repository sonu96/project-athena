"""
Workflow State Management

Defines the consciousness state that flows through the cognitive loop.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from ..core.emotions import EmotionalState


class ConsciousnessState(BaseModel):
    """
    Enhanced consciousness state for the Athena agent
    
    This state flows through the entire cognitive loop and contains
    all the information needed for decision making.
    """
    
    # Identity
    agent_id: str = Field(default="athena-v1")
    timestamp: datetime = Field(default_factory=datetime.now)
    cycle_count: int = Field(default=0)
    
    # Treasury and Economics
    treasury_balance: float = Field(default=100.0)
    daily_burn_rate: float = Field(default=0.0)
    days_until_bankruptcy: float = Field(default=999.0)
    
    # Emotional Intelligence
    emotional_state: EmotionalState = Field(default=EmotionalState.STABLE)
    emotional_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_level: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Market Observations
    market_data: Dict[str, Any] = Field(default_factory=dict)
    observed_pools: List[Dict[str, Any]] = Field(default_factory=list)
    gas_price: float = Field(default=20.0)
    
    # Memory and Learning
    recent_memories: List[Dict[str, Any]] = Field(default_factory=list)
    active_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    memory_formation_threshold: float = Field(default=0.7)
    
    # Decision Context
    last_decision: Optional[Dict[str, Any]] = Field(default=None)
    pending_observations: List[str] = Field(default_factory=list)
    observation_priority: int = Field(default=1)
    
    # Operational
    total_cost: float = Field(default=0.0)
    cycle_cost: float = Field(default=0.0)
    llm_model: str = Field(default="gemini-1.5-flash-002")
    
    # Status and Errors
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    health_status: str = Field(default="healthy")
    
    # Workflow Control
    next_action: str = Field(default="sense")
    workflow_complete: bool = Field(default=False)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            EmotionalState: lambda v: v.value
        }
    
    def add_observation(self, pool_data: Dict[str, Any]) -> None:
        """Add pool observation to state"""
        self.observed_pools.append({
            **pool_data,
            "observed_at": datetime.now().isoformat()
        })
    
    def add_memory(self, memory: Dict[str, Any]) -> None:
        """Add memory to recent memories"""
        self.recent_memories.append({
            **memory,
            "added_at": datetime.now().isoformat()
        })
    
    def add_pattern(self, pattern: Dict[str, Any]) -> None:
        """Add recognized pattern"""
        self.active_patterns.append({
            **pattern,
            "recognized_at": datetime.now().isoformat()
        })
    
    def add_error(self, error: str) -> None:
        """Add error to state"""
        self.errors.append(f"{datetime.now().isoformat()}: {error}")
    
    def add_warning(self, warning: str) -> None:
        """Add warning to state"""
        self.warnings.append(f"{datetime.now().isoformat()}: {warning}")
    
    def increment_cycle(self) -> None:
        """Increment cycle count and reset cycle-specific data"""
        self.cycle_count += 1
        self.cycle_cost = 0.0
        self.timestamp = datetime.now()
    
    def add_cost(self, cost: float, description: str = "") -> None:
        """Add cost to total and cycle costs"""
        self.cycle_cost += cost
        self.total_cost += cost
        if description:
            self.add_warning(f"Cost: ${cost:.4f} - {description}")
    
    def should_continue_cycle(self) -> bool:
        """Determine if cycle should continue"""
        # Don't continue if we have critical errors
        if any("critical" in error.lower() for error in self.errors):
            return False
        
        # Don't continue if we're bankrupt
        if self.treasury_balance <= 0:
            return False
        
        # Don't continue if workflow is marked complete
        if self.workflow_complete:
            return False
        
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get state summary for logging"""
        return {
            "cycle": self.cycle_count,
            "emotional_state": self.emotional_state.value,
            "treasury": f"${self.treasury_balance:.2f}",
            "cycle_cost": f"${self.cycle_cost:.4f}",
            "total_cost": f"${self.total_cost:.4f}",
            "observations": len(self.observed_pools),
            "memories": len(self.recent_memories),
            "patterns": len(self.active_patterns),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "health": self.health_status
        }
    
    def to_firestore_doc(self) -> Dict[str, Any]:
        """Convert to Firestore document format"""
        doc = self.dict()
        
        # Convert datetime objects
        doc["timestamp"] = self.timestamp.isoformat()
        
        # Convert enum
        doc["emotional_state"] = self.emotional_state.value
        
        # Limit array sizes for Firestore
        doc["observed_pools"] = self.observed_pools[-10:]  # Last 10
        doc["recent_memories"] = self.recent_memories[-20:]  # Last 20
        doc["active_patterns"] = self.active_patterns[-10:]  # Last 10
        doc["errors"] = self.errors[-20:]  # Last 20
        doc["warnings"] = self.warnings[-20:]  # Last 20
        
        return doc