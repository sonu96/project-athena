"""
Position data models for DeFi yield optimization
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class PositionStatus(Enum):
    """Status of a DeFi position"""
    ACTIVE = "active"
    PENDING_EXIT = "pending_exit"
    EXITED = "exited"
    FAILED = "failed"


@dataclass
class Position:
    """Represents an active DeFi position"""
    position_id: str
    protocol: str
    chain: str
    pool_address: str
    pool_name: str
    position_type: str  # 'stable_lp', 'volatile_lp', 'lending', 'staking'
    amount_usd: float
    amount_tokens: Dict[str, float]
    entry_timestamp: datetime
    entry_apy: float
    current_apy: float
    accumulated_rewards_usd: float
    accumulated_rewards_tokens: Dict[str, float]
    last_compound: Optional[datetime]
    il_exposure: float  # Impermanent loss exposure (0-1)
    risk_score: float  # 0-1, higher is riskier
    exit_strategy: str
    position_memories: List[str]
    status: PositionStatus = PositionStatus.ACTIVE
    gas_spent_usd: float = 0.0
    
    @property
    def net_value_usd(self) -> float:
        """Calculate net value including rewards minus gas"""
        return self.amount_usd + self.accumulated_rewards_usd - self.gas_spent_usd
    
    @property
    def roi_percent(self) -> float:
        """Calculate return on investment percentage"""
        if self.amount_usd == 0:
            return 0.0
        return ((self.net_value_usd - self.amount_usd) / self.amount_usd) * 100
    
    @property
    def should_compound(self) -> bool:
        """Determine if position should be compounded based on rewards"""
        # Compound if rewards > $10 or > 5% of position
        return (self.accumulated_rewards_usd > 10.0 or 
                self.accumulated_rewards_usd > self.amount_usd * 0.05)
    
    @property
    def health_score(self) -> float:
        """Calculate position health (0-1, higher is healthier)"""
        factors = []
        
        # APY consistency
        if self.entry_apy > 0:
            apy_ratio = min(self.current_apy / self.entry_apy, 2.0)
            factors.append(apy_ratio * 0.3)
        
        # Risk factor (inverted)
        factors.append((1 - self.risk_score) * 0.3)
        
        # ROI factor
        roi_factor = min(max(self.roi_percent / 20, 0), 1)  # 20% ROI = perfect score
        factors.append(roi_factor * 0.4)
        
        return sum(factors)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'position_id': self.position_id,
            'protocol': self.protocol,
            'chain': self.chain,
            'pool_address': self.pool_address,
            'pool_name': self.pool_name,
            'position_type': self.position_type,
            'amount_usd': self.amount_usd,
            'amount_tokens': self.amount_tokens,
            'entry_timestamp': self.entry_timestamp.isoformat(),
            'entry_apy': self.entry_apy,
            'current_apy': self.current_apy,
            'accumulated_rewards_usd': self.accumulated_rewards_usd,
            'accumulated_rewards_tokens': self.accumulated_rewards_tokens,
            'last_compound': self.last_compound.isoformat() if self.last_compound else None,
            'il_exposure': self.il_exposure,
            'risk_score': self.risk_score,
            'exit_strategy': self.exit_strategy,
            'position_memories': self.position_memories,
            'status': self.status.value,
            'gas_spent_usd': self.gas_spent_usd,
            'net_value_usd': self.net_value_usd,
            'roi_percent': self.roi_percent,
            'health_score': self.health_score
        }