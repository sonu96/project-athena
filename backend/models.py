from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class MemoryType(Enum):
    SURVIVAL = "survival"
    STRATEGY = "strategy"
    MARKET = "market"
    PROTOCOL = "protocol"

class TreasuryEntry(BaseModel):
    timestamp: datetime
    balance: float
    change: float
    reason: str
    gas_cost: Optional[float] = None

class MemoryEntry(BaseModel):
    id: str
    type: MemoryType
    timestamp: datetime
    data: Dict[str, Any]
    importance_score: float = Field(ge=0.0, le=1.0)
    success_outcome: Optional[bool] = None
    context: Dict[str, Any] = {}

class AgentState(BaseModel):
    treasury_balance: float
    survival_status: str  # "STABLE", "CAUTION", "WARNING", "CRITICAL"
    days_until_bankruptcy: float
    daily_burn_rate: float
    memory_count: int
    last_decision: Optional[datetime] = None

class DecisionContext(BaseModel):
    current_treasury: float
    market_condition: str
    available_protocols: List[str]
    gas_price: float
    risk_tolerance: float = Field(ge=0.0, le=1.0)

class DecisionResult(BaseModel):
    action: str
    protocol: Optional[str] = None
    amount: Optional[float] = None
    expected_yield: Optional[float] = None
    risk_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    treasury_impact: float
    timestamp: datetime = Field(default_factory=datetime.now)

class MemoryQuery(BaseModel):
    query_type: MemoryType
    context: Dict[str, Any]
    importance_threshold: float = 0.5
    limit: int = 10 