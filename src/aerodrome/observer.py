"""
Aerodrome Observer - V1 Read-Only Implementation

Observes Aerodrome Finance pools without executing trades.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import random

from .pools import PoolData, PoolType
from ..config.constants import AERODROME_FACTORY_ADDRESS, AERODROME_ROUTER_ADDRESS

logger = logging.getLogger(__name__)


class AerodromeObserver:
    """
    Observes Aerodrome Finance pools for patterns and opportunities
    
    V1 Features:
    - Pool discovery and monitoring
    - TVL and volume tracking
    - Yield calculation
    - Pattern identification
    
    V2 will add:
    - Position entry/exit
    - Leverage management
    - Actual trading
    """
    
    def __init__(self, cdp_client=None):
        self.observed_pools: Dict[str, PoolData] = {}
        self.observation_history: List[Dict[str, Any]] = []
        
        # Use CDP client for contract interactions
        self.cdp_client = cdp_client
        self.simulation_mode = cdp_client is None or cdp_client.simulation_mode
        
        # Aerodrome contract addresses
        self.factory_address = AERODROME_FACTORY_ADDRESS
        self.router_address = AERODROME_ROUTER_ADDRESS
        
        logger.info(f"🔍 Aerodrome Observer initialized (Mode: {'Simulation' if self.simulation_mode else 'Live CDP'})")
    
    async def get_top_pools(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top pools by TVL
        
        Uses CDP to query Aerodrome factory for real pool data
        """
        if self.simulation_mode:
            return self._generate_simulated_pools(limit)
        
        try:
            # Get total pool count from factory
            pool_count = await self._get_pool_count()
            if not pool_count:
                logger.warning("Could not get pool count from Aerodrome")
                return []
            
            logger.info(f"Aerodrome has {pool_count} pools total")
            
            # Get recent pools (last N pools)
            pools = []
            start_idx = max(0, pool_count - limit * 2)  # Get more to filter
            
            for i in range(start_idx, min(pool_count, start_idx + limit * 2)):
                pool_data = await self._fetch_pool_by_index(i)
                if pool_data and pool_data["tvl_usd"] > 10000:  # Min $10k TVL
                    pools.append(pool_data)
                    if len(pools) >= limit:
                        break
            
            # Sort by TVL
            pools.sort(key=lambda p: p["tvl_usd"], reverse=True)
            
            return pools[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get top pools: {e}")
            return self._generate_simulated_pools(limit)
    
    async def observe_pool(self, pool_address: str) -> Optional[PoolData]:
        """
        Observe a specific pool
        
        Args:
            pool_address: Pool contract address
            
        Returns:
            Pool data if available
        """
        try:
            if self.simulation_mode:
                # Generate simulated observation
                pool_data = self._generate_pool_observation(pool_address)
            else:
                # V2: Actual pool query
                pool_data = await self._fetch_pool_data(pool_address)
            
            if pool_data:
                # Update cache
                self.observed_pools[pool_address] = pool_data
                
                # Record observation
                self._record_observation(pool_data)
                
                logger.debug(f"Observed pool {pool_data.pair_name}: TVL ${pool_data.tvl_usd:,.0f}")
            
            return pool_data
            
        except Exception as e:
            logger.error(f"Failed to observe pool {pool_address}: {e}")
            return None
    
    async def calculate_pool_yield(self, pool_data: PoolData) -> Dict[str, float]:
        """
        Calculate expected yields for a pool
        
        Returns:
            Dict with yield components
        """
        # Fee APY calculation
        if pool_data.tvl_usd > 0:
            # Simplified: assume fees proportional to volume
            daily_fees = pool_data.volume_24h_usd * pool_data.fee_tier
            annual_fees = daily_fees * 365
            fee_apy = annual_fees / pool_data.tvl_usd
        else:
            fee_apy = 0.0
        
        # Update pool data
        pool_data.fee_apy = fee_apy
        
        return {
            "fee_apy": fee_apy,
            "reward_apy": pool_data.reward_apy,
            "total_apy": fee_apy + pool_data.reward_apy,
            "daily_yield": (fee_apy + pool_data.reward_apy) / 365
        }
    
    def identify_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify observation-worthy opportunities
        
        Returns:
            List of opportunities with reasoning
        """
        opportunities = []
        
        for address, pool in self.observed_pools.items():
            # High yield opportunity
            if pool.is_high_yield():
                opportunities.append({
                    "type": "high_yield",
                    "pool": pool.pair_name,
                    "apy": pool.total_apy,
                    "reason": f"High yield pool with {pool.total_apy:.1%} APY",
                    "risk": "Check for sustainability"
                })
            
            # High volume opportunity
            if pool.volume_tvl_ratio > 0.5:  # 50% daily volume
                opportunities.append({
                    "type": "high_volume",
                    "pool": pool.pair_name,
                    "volume_ratio": pool.volume_tvl_ratio,
                    "reason": f"High activity with {pool.volume_tvl_ratio:.1%} daily volume/TVL",
                    "risk": "May indicate volatility"
                })
            
            # Stable opportunity
            if pool.pool_type == PoolType.STABLE and pool.fee_apy > 0.05:
                opportunities.append({
                    "type": "stable_yield",
                    "pool": pool.pair_name,
                    "apy": pool.fee_apy,
                    "reason": f"Stable pool with {pool.fee_apy:.1%} fee yield",
                    "risk": "Lower but consistent returns"
                })
        
        return opportunities
    
    def get_observation_summary(self) -> Dict[str, Any]:
        """Get summary of observations"""
        
        if not self.observed_pools:
            return {"status": "No pools observed yet"}
        
        total_tvl = sum(p.tvl_usd for p in self.observed_pools.values())
        total_volume = sum(p.volume_24h_usd for p in self.observed_pools.values())
        avg_apy = sum(p.total_apy for p in self.observed_pools.values()) / len(self.observed_pools)
        
        return {
            "pools_observed": len(self.observed_pools),
            "total_tvl_usd": total_tvl,
            "total_volume_24h_usd": total_volume,
            "average_apy": avg_apy,
            "top_yield_pool": max(self.observed_pools.values(), key=lambda p: p.total_apy).pair_name,
            "top_volume_pool": max(self.observed_pools.values(), key=lambda p: p.volume_24h_usd).pair_name,
            "observations_count": len(self.observation_history)
        }
    
    def _generate_simulated_pools(self, limit: int) -> List[Dict[str, Any]]:
        """Generate simulated pool data for V1"""
        
        # Common pool pairs on Aerodrome
        pool_configs = [
            ("USDC", "ETH", PoolType.VOLATILE, 15_000_000, 0.003),
            ("USDC", "USDT", PoolType.STABLE, 50_000_000, 0.0005),
            ("ETH", "WBTC", PoolType.VOLATILE, 8_000_000, 0.003),
            ("WETH", "AERO", PoolType.VOLATILE, 5_000_000, 0.003),
            ("USDC", "DAI", PoolType.STABLE, 20_000_000, 0.0005),
            ("ETH", "stETH", PoolType.STABLE, 30_000_000, 0.0005),
            ("USDC", "AERO", PoolType.VOLATILE, 3_000_000, 0.01),
            ("WBTC", "tBTC", PoolType.STABLE, 10_000_000, 0.0005),
        ]
        
        pools = []
        for i, (token0, token1, pool_type, base_tvl, fee_tier) in enumerate(pool_configs[:limit]):
            # Add some randomness
            tvl_variation = random.uniform(0.8, 1.2)
            volume_ratio = random.uniform(0.05, 0.4)  # 5-40% daily volume
            
            tvl = base_tvl * tvl_variation
            volume_24h = tvl * volume_ratio
            
            # Calculate yields
            fee_apy = (volume_24h * fee_tier * 365) / tvl
            reward_apy = random.uniform(0.02, 0.15)  # 2-15% AERO rewards
            
            pools.append({
                "address": f"0x{i:040x}",
                "type": pool_type.value,
                "token0_symbol": token0,
                "token1_symbol": token1,
                "tvl_usd": tvl,
                "volume_24h_usd": volume_24h,
                "fee_tier": fee_tier,
                "fee_apy": fee_apy,
                "reward_apy": reward_apy,
                "total_apy": fee_apy + reward_apy
            })
        
        # Sort by TVL
        pools.sort(key=lambda p: p["tvl_usd"], reverse=True)
        
        return pools
    
    def _generate_pool_observation(self, pool_address: str) -> PoolData:
        """Generate simulated pool observation"""
        
        # Use address to seed randomness (for consistency)
        random.seed(pool_address)
        
        # Random pool configuration
        pairs = [
            ("USDC", "ETH", PoolType.VOLATILE),
            ("USDC", "USDT", PoolType.STABLE),
            ("ETH", "WBTC", PoolType.VOLATILE),
            ("WETH", "AERO", PoolType.VOLATILE)
        ]
        
        token0, token1, pool_type = random.choice(pairs)
        
        # Generate metrics
        tvl = random.uniform(1_000_000, 50_000_000)
        volume_24h = tvl * random.uniform(0.05, 0.4)
        fee_tier = 0.003 if pool_type == PoolType.VOLATILE else 0.0005
        
        fee_apy = (volume_24h * fee_tier * 365) / tvl
        reward_apy = random.uniform(0.02, 0.15)
        
        return PoolData(
            address=pool_address,
            pool_type=pool_type,
            token0_address=f"0x{token0}",
            token0_symbol=token0,
            token0_decimals=18,
            token1_address=f"0x{token1}",
            token1_symbol=token1,
            token1_decimals=18,
            tvl_usd=tvl,
            volume_24h_usd=volume_24h,
            volume_7d_usd=volume_24h * 7 * random.uniform(0.8, 1.2),
            fee_tier=fee_tier,
            fee_apy=fee_apy,
            reward_apy=reward_apy,
            total_apy=fee_apy + reward_apy,
            observation_time=datetime.utcnow()
        )
    
    def _record_observation(self, pool_data: PoolData):
        """Record observation for pattern analysis"""
        
        observation = {
            "timestamp": datetime.utcnow(),
            "pool_address": pool_data.address,
            "pair": pool_data.pair_name,
            "tvl_usd": pool_data.tvl_usd,
            "volume_24h_usd": pool_data.volume_24h_usd,
            "total_apy": pool_data.total_apy,
            "volume_tvl_ratio": pool_data.volume_tvl_ratio
        }
        
        self.observation_history.append(observation)
        
        # Keep only last 1000 observations
        if len(self.observation_history) > 1000:
            self.observation_history = self.observation_history[-1000:]
    
    async def _get_pool_count(self) -> Optional[int]:
        """Get total number of pools from Aerodrome factory using CDP"""
        try:
            abi = {
                "inputs": [],
                "name": "allPoolsLength",
                "outputs": [{"type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
            
            result = await self.cdp_client.read_contract(
                contract_address=self.factory_address,
                method="allPoolsLength",
                abi=abi
            )
            
            return int(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to get pool count: {e}")
            return None
    
    async def _fetch_pool_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Fetch pool data by index from factory"""
        try:
            # Get pool address
            pool_address = await self._get_pool_address(index)
            if not pool_address:
                return None
            
            # Get pool data
            return await self._fetch_pool_data(pool_address)
            
        except Exception as e:
            logger.error(f"Failed to fetch pool by index {index}: {e}")
            return None
    
    async def _get_pool_address(self, index: int) -> Optional[str]:
        """Get pool address by index from factory"""
        try:
            abi = {
                "inputs": [{"type": "uint256"}],
                "name": "allPools",
                "outputs": [{"type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
            
            result = await self.cdp_client.read_contract(
                contract_address=self.factory_address,
                method="allPools",
                abi=abi,
                args=[index]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get pool address: {e}")
            return None
    
    async def _fetch_pool_data(self, pool_address: str) -> Optional[Dict[str, Any]]:
        """Fetch actual pool data from blockchain using CDP"""
        try:
            # Get token addresses
            token0 = await self._read_pool_method(pool_address, "token0", [{"type": "address"}])
            token1 = await self._read_pool_method(pool_address, "token1", [{"type": "address"}])
            
            # Get reserves
            reserves_result = await self._read_pool_method(
                pool_address, 
                "getReserves",
                [
                    {"type": "uint256", "name": "_reserve0"},
                    {"type": "uint256", "name": "_reserve1"},
                    {"type": "uint256", "name": "_blockTimestampLast"}
                ]
            )
            
            if not reserves_result:
                return None
            
            # Get pool type (stable/volatile)
            is_stable = await self._read_pool_method(pool_address, "stable", [{"type": "bool"}])
            
            # Get token symbols
            token0_symbol = await self._get_token_symbol(token0)
            token1_symbol = await self._get_token_symbol(token1)
            
            # Calculate TVL (simplified - would need price oracle)
            # For now, assume USDC = $1 and estimate others
            tvl_usd = self._estimate_tvl(token0, token1, reserves_result[0], reserves_result[1])
            
            # Build pool data
            pool_type = PoolType.STABLE if is_stable else PoolType.VOLATILE
            
            return {
                "address": pool_address,
                "type": pool_type.value,
                "token0_symbol": token0_symbol,
                "token1_symbol": token1_symbol,
                "token0_address": token0,
                "token1_address": token1,
                "reserve0": reserves_result[0],
                "reserve1": reserves_result[1],
                "tvl_usd": tvl_usd,
                "volume_24h_usd": tvl_usd * 0.1,  # Estimate 10% daily volume
                "fee_tier": 0.0005 if is_stable else 0.003,
                "fee_apy": 0.05,  # Placeholder
                "reward_apy": 0.10,  # Placeholder
                "total_apy": 0.15,  # Placeholder
                "symbol": f"{token0_symbol}/{token1_symbol}"
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch pool data for {pool_address}: {e}")
            return None
    
    async def _read_pool_method(self, pool_address: str, method: str, outputs: list) -> Any:
        """Read a method from pool contract"""
        try:
            abi = {
                "inputs": [],
                "name": method,
                "outputs": outputs,
                "stateMutability": "view",
                "type": "function"
            }
            
            return await self.cdp_client.read_contract(
                contract_address=pool_address,
                method=method,
                abi=abi
            )
            
        except Exception as e:
            logger.error(f"Failed to read {method} from {pool_address}: {e}")
            return None
    
    async def _get_token_symbol(self, token_address: str) -> str:
        """Get token symbol using CDP"""
        try:
            abi = {
                "inputs": [],
                "name": "symbol",
                "outputs": [{"type": "string"}],
                "stateMutability": "view",
                "type": "function"
            }
            
            symbol = await self.cdp_client.read_contract(
                contract_address=token_address,
                method="symbol",
                abi=abi
            )
            
            return symbol or "???"
            
        except:
            # Try to identify known tokens
            known_tokens = {
                "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": "USDC",
                "0x4200000000000000000000000000000000000006": "WETH",
                "0x940181a94A35A4569E4529A3CDfB74e38FD98631": "AERO",
                "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb": "DAI",
            }
            return known_tokens.get(token_address.lower(), "???")
    
    def _estimate_tvl(self, token0: str, token1: str, reserve0: int, reserve1: int) -> float:
        """Estimate TVL in USD (simplified)"""
        # Known stablecoins
        stablecoins = {
            "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
            "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",  # DAI
        }
        
        # Simplified: if one token is stablecoin, use its value * 2
        if token0.lower() in stablecoins:
            return (reserve0 / 1e6) * 2  # USDC has 6 decimals
        elif token1.lower() in stablecoins:
            return (reserve1 / 1e6) * 2
        else:
            # Rough estimate for other pairs
            return 100000  # Placeholder
    
    async def _fetch_pool_data_old(self, pool_address: str) -> Optional[PoolData]:
        """V2: Fetch actual pool data from blockchain"""
        # Keeping old implementation for reference
        pass