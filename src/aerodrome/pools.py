"""
Pool data structures for Aerodrome Finance
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class PoolType(Enum):
    """Aerodrome pool types"""
    STABLE = "stable"      # For correlated assets
    VOLATILE = "volatile"  # For uncorrelated assets


@dataclass
class PoolData:
    """Data structure for Aerodrome pool information"""
    
    # Identifiers
    address: str
    pool_type: PoolType
    
    # Token information
    token0_address: str
    token0_symbol: str
    token0_decimals: int
    token1_address: str
    token1_symbol: str
    token1_decimals: int
    
    # Pool metrics
    tvl_usd: float
    volume_24h_usd: float
    volume_7d_usd: float
    
    # Yield metrics
    fee_tier: float        # Fee percentage (e.g., 0.003 = 0.3%)
    fee_apy: float         # Annualized fee yield
    reward_apy: float      # AERO rewards APY
    total_apy: float       # Combined APY
    
    # Additional data
    tick: Optional[int] = None
    liquidity: Optional[float] = None
    observation_time: Optional[datetime] = None
    
    @property
    def pair_name(self) -> str:
        """Get human-readable pair name"""
        return f"{self.token0_symbol}/{self.token1_symbol}"
    
    @property
    def volume_tvl_ratio(self) -> float:
        """Calculate 24h volume to TVL ratio"""
        if self.tvl_usd > 0:
            return self.volume_24h_usd / self.tvl_usd
        return 0.0
    
    def is_high_yield(self, threshold: float = 0.3) -> bool:
        """Check if pool has high yield"""
        return self.total_apy >= threshold
    
    def is_active(self, min_volume: float = 100000) -> bool:
        """Check if pool has sufficient activity"""
        return self.volume_24h_usd >= min_volume