"""
Opportunity data models for DeFi yield optimization
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from enum import Enum


class OpportunityType(Enum):
    """Type of yield opportunity"""
    LENDING = "lending"
    STABLE_LP = "stable_lp"
    VOLATILE_LP = "volatile_lp"
    STAKING = "staking"
    BRIDGE_ARBITRAGE = "bridge_arbitrage"


@dataclass
class YieldOpportunity:
    """Represents a yield opportunity"""
    opportunity_id: str
    timestamp: datetime
    protocol: str
    chain: str
    pool_address: str
    asset: str  # Primary asset or pool name
    opportunity_type: OpportunityType
    current_apy: float
    apy_base: float
    apy_rewards: float
    tvl_usd: float
    utilization_rate: float
    risk_score: float  # 0-1, higher is riskier
    gas_to_enter: float  # Estimated gas cost in USD
    min_profitable_duration_days: float
    discovered_by: str  # Which system/scan discovered this
    priority_score: float  # 0-1, higher priority first
    
    @property
    def risk_adjusted_apy(self) -> float:
        """Calculate risk-adjusted APY"""
        return self.current_apy * (1 - self.risk_score)
    
    @property
    def breakeven_days(self) -> float:
        """Days to break even on gas costs"""
        if self.current_apy == 0:
            return float('inf')
        daily_yield_rate = self.current_apy / 365 / 100
        return self.gas_to_enter / (1000 * daily_yield_rate)  # Assuming $1000 position
    
    @property
    def attractiveness_score(self) -> float:
        """Calculate overall attractiveness (0-1)"""
        factors = []
        
        # APY factor (normalized to 0-50% range)
        apy_factor = min(self.current_apy / 50, 1.0) * 0.3
        factors.append(apy_factor)
        
        # Risk factor (inverted)
        risk_factor = (1 - self.risk_score) * 0.3
        factors.append(risk_factor)
        
        # TVL factor (higher is better, log scale)
        import math
        tvl_factor = min(math.log10(max(self.tvl_usd, 1)) / 8, 1.0) * 0.2  # $100M = 1.0
        factors.append(tvl_factor)
        
        # Gas efficiency factor
        gas_factor = max(1 - (self.gas_to_enter / 10), 0) * 0.2  # $10 gas = 0
        factors.append(gas_factor)
        
        return sum(factors)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'opportunity_id': self.opportunity_id,
            'timestamp': self.timestamp.isoformat(),
            'protocol': self.protocol,
            'chain': self.chain,
            'pool_address': self.pool_address,
            'asset': self.asset,
            'opportunity_type': self.opportunity_type.value,
            'current_apy': self.current_apy,
            'apy_base': self.apy_base,
            'apy_rewards': self.apy_rewards,
            'tvl_usd': self.tvl_usd,
            'utilization_rate': self.utilization_rate,
            'risk_score': self.risk_score,
            'gas_to_enter': self.gas_to_enter,
            'min_profitable_duration_days': self.min_profitable_duration_days,
            'discovered_by': self.discovered_by,
            'priority_score': self.priority_score,
            'risk_adjusted_apy': self.risk_adjusted_apy,
            'breakeven_days': self.breakeven_days,
            'attractiveness_score': self.attractiveness_score
        }


@dataclass
class BridgeOpportunity:
    """Represents a cross-chain arbitrage opportunity"""
    opportunity_id: str
    timestamp: datetime
    asset: str
    source_chain: str
    source_protocol: str
    source_apy: float
    target_chain: str
    target_protocol: str
    target_apy: float
    bridge_protocol: str
    bridge_cost_usd: float
    bridge_time_minutes: int
    net_apy_gain: float
    amount_for_profitability: float  # Min amount to make it profitable
    risk_adjusted_score: float
    
    @property
    def is_profitable(self) -> bool:
        """Check if opportunity is profitable after costs"""
        return self.net_apy_gain > 0 and self.risk_adjusted_score > 0.5
    
    @property
    def daily_profit_usd(self) -> float:
        """Estimated daily profit for $1000 position"""
        if not self.is_profitable:
            return 0.0
        return (1000 * self.net_apy_gain / 365 / 100) - (self.bridge_cost_usd / 30)  # Amortize bridge cost over 30 days
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'opportunity_id': self.opportunity_id,
            'timestamp': self.timestamp.isoformat(),
            'asset': self.asset,
            'source_chain': self.source_chain,
            'source_protocol': self.source_protocol,
            'source_apy': self.source_apy,
            'target_chain': self.target_chain,
            'target_protocol': self.target_protocol,
            'target_apy': self.target_apy,
            'bridge_protocol': self.bridge_protocol,
            'bridge_cost_usd': self.bridge_cost_usd,
            'bridge_time_minutes': self.bridge_time_minutes,
            'net_apy_gain': self.net_apy_gain,
            'amount_for_profitability': self.amount_for_profitability,
            'risk_adjusted_score': self.risk_adjusted_score,
            'is_profitable': self.is_profitable,
            'daily_profit_usd': self.daily_profit_usd
        }