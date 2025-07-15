"""
Event data models for tracking yield optimization activities
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class RebalanceReason(Enum):
    """Reasons for rebalancing positions"""
    LOW_APY = "low_apy"
    HIGH_RISK = "high_risk"
    BETTER_OPPORTUNITY = "better_opportunity"
    RISK_EVENT = "risk_event"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class RiskEventType(Enum):
    """Types of risk events"""
    HACK = "hack"
    RUG_PULL = "rug"
    DEPEG = "depeg"
    HIGH_IL = "high_il"
    TVL_EXODUS = "tvl_exodus"
    SMART_CONTRACT_BUG = "smart_contract_bug"


class RiskSeverity(Enum):
    """Severity levels for risk events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RebalanceEvent:
    """Tracks position rebalancing activities"""
    rebalance_id: str
    timestamp: datetime
    source_position_id: str
    target_position_id: Optional[str]  # None if just exiting
    source_protocol: str
    target_protocol: Optional[str]
    source_chain: str
    target_chain: Optional[str]
    amount_moved_usd: float
    gas_cost_usd: float
    bridge_cost_usd: float
    source_apy_at_exit: float
    target_apy_at_entry: Optional[float]
    rebalance_reason: RebalanceReason
    success: bool
    net_gain_loss_usd: float
    execution_time_seconds: int
    memory_formation: Optional[str]
    error_message: Optional[str] = None
    
    @property
    def total_cost(self) -> float:
        """Total cost of rebalancing"""
        return self.gas_cost_usd + self.bridge_cost_usd
    
    @property
    def was_profitable(self) -> bool:
        """Check if rebalance was ultimately profitable"""
        return self.net_gain_loss_usd > self.total_cost
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'rebalance_id': self.rebalance_id,
            'timestamp': self.timestamp.isoformat(),
            'source_position_id': self.source_position_id,
            'target_position_id': self.target_position_id,
            'source_protocol': self.source_protocol,
            'target_protocol': self.target_protocol,
            'source_chain': self.source_chain,
            'target_chain': self.target_chain,
            'amount_moved_usd': self.amount_moved_usd,
            'gas_cost_usd': self.gas_cost_usd,
            'bridge_cost_usd': self.bridge_cost_usd,
            'source_apy_at_exit': self.source_apy_at_exit,
            'target_apy_at_entry': self.target_apy_at_entry,
            'rebalance_reason': self.rebalance_reason.value,
            'success': self.success,
            'net_gain_loss_usd': self.net_gain_loss_usd,
            'execution_time_seconds': self.execution_time_seconds,
            'memory_formation': self.memory_formation,
            'error_message': self.error_message,
            'total_cost': self.total_cost,
            'was_profitable': self.was_profitable
        }


@dataclass
class CompoundEvent:
    """Tracks compound operations"""
    compound_id: str
    timestamp: datetime
    position_id: str
    protocol: str
    chain: str
    rewards_claimed_usd: float
    rewards_claimed_tokens: Dict[str, float]
    gas_cost_usd: float
    compound_profitable: bool
    days_since_last_compound: float
    position_size_usd: float
    gas_price_gwei: float
    batched_with: List[str]  # Other positions compounded in same tx
    compound_strategy: str  # 'scheduled', 'threshold', 'gas_optimized'
    
    @property
    def net_rewards_usd(self) -> float:
        """Net rewards after gas costs"""
        return self.rewards_claimed_usd - self.gas_cost_usd
    
    @property
    def efficiency_score(self) -> float:
        """Compound efficiency (0-1)"""
        if self.rewards_claimed_usd == 0:
            return 0.0
        return max(0, min(1, self.net_rewards_usd / self.rewards_claimed_usd))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'compound_id': self.compound_id,
            'timestamp': self.timestamp.isoformat(),
            'position_id': self.position_id,
            'protocol': self.protocol,
            'chain': self.chain,
            'rewards_claimed_usd': self.rewards_claimed_usd,
            'rewards_claimed_tokens': self.rewards_claimed_tokens,
            'gas_cost_usd': self.gas_cost_usd,
            'compound_profitable': self.compound_profitable,
            'days_since_last_compound': self.days_since_last_compound,
            'position_size_usd': self.position_size_usd,
            'gas_price_gwei': self.gas_price_gwei,
            'batched_with': self.batched_with,
            'compound_strategy': self.compound_strategy,
            'net_rewards_usd': self.net_rewards_usd,
            'efficiency_score': self.efficiency_score
        }


@dataclass
class RiskEvent:
    """Tracks detected risks and mitigation actions"""
    event_id: str
    timestamp: datetime
    event_type: RiskEventType
    severity: RiskSeverity
    protocol: str
    chain: str
    detected_indicators: Dict[str, Any]
    action_taken: str  # 'exit_position', 'reduce_exposure', 'monitor', 'ignore'
    position_exited: bool
    loss_avoided_usd: float
    false_positive: bool
    memory_importance: float
    lessons_learned: str
    affected_positions: List[str]
    
    @property
    def was_accurate(self) -> bool:
        """Check if risk detection was accurate"""
        return not self.false_positive and self.loss_avoided_usd > 0
    
    @property
    def response_effectiveness(self) -> float:
        """Rate effectiveness of response (0-1)"""
        if self.false_positive:
            return 0.0
        if self.severity == RiskSeverity.CRITICAL and self.position_exited:
            return 1.0
        if self.severity == RiskSeverity.HIGH and self.loss_avoided_usd > 100:
            return 0.8
        if self.severity == RiskSeverity.MEDIUM and self.loss_avoided_usd > 50:
            return 0.6
        return 0.3
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'protocol': self.protocol,
            'chain': self.chain,
            'detected_indicators': self.detected_indicators,
            'action_taken': self.action_taken,
            'position_exited': self.position_exited,
            'loss_avoided_usd': self.loss_avoided_usd,
            'false_positive': self.false_positive,
            'memory_importance': self.memory_importance,
            'lessons_learned': self.lessons_learned,
            'affected_positions': self.affected_positions,
            'was_accurate': self.was_accurate,
            'response_effectiveness': self.response_effectiveness
        }