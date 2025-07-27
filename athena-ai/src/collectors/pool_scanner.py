"""
Aerodrome Pool Scanner
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from src.cdp.base_client import BaseClient
from src.agent.memory import AthenaMemory, MemoryType
from src.aerodrome.event_monitor import EventMonitor
from config.contracts import TOKENS

logger = logging.getLogger(__name__)


class PoolScanner:
    """
    Scans Aerodrome pools for opportunities.
    
    Monitors liquidity pools, tracks APRs, volumes, and identifies
    profitable opportunities for liquidity provision and trading.
    """
    
    def __init__(self, base_client: BaseClient, memory: AthenaMemory):
        """Initialize pool scanner."""
        self.base_client = base_client
        self.memory = memory
        self.scanning = False
        
        # Pool data cache
        self.pools = {}
        self.last_scan = None
        
        # Top opportunities
        self.opportunities = {
            "high_apr": [],
            "high_volume": [],
            "new_pools": [],
            "imbalanced": [],
        }
        
        # Event monitor for volume tracking (temporarily disabled)
        self.event_monitor = None
        
    async def start_scanning(self):
        """Start continuous pool scanning."""
        if self.scanning:
            logger.warning("Pool scanning already active")
            return
            
        self.scanning = True
        logger.info("=== Starting Aerodrome pool scanning...")
        
        while self.scanning:
            try:
                await self._scan_cycle()
                await asyncio.sleep(300)  # Scan every 5 minutes
                
            except Exception as e:
                logger.error(f"Pool scanning error: {e}")
                await asyncio.sleep(600)  # Wait longer on error
                
    async def stop_scanning(self):
        """Stop pool scanning."""
        self.scanning = False
        logger.info("Pool scanning stopped")
        
    async def _scan_cycle(self):
        """Single scanning cycle."""
        logger.info("Scanning Aerodrome pools...")
        
        # Pre-fetch common token prices to populate cache
        logger.info("Pre-fetching token prices...")
        try:
            # Fetch prices for major tokens
            await self.base_client.get_token_price_usd(TOKENS["WETH"])
            await self.base_client.get_token_price_usd(TOKENS["AERO"])
            # USDC, DAI, USDbC are stablecoins, will be cached as $1
            await self.base_client.get_token_price_usd(TOKENS["USDC"])
            await self.base_client.get_token_price_usd(TOKENS["DAI"])
            await self.base_client.get_token_price_usd(TOKENS["USDbC"])
            logger.info("Token prices cached successfully")
        except Exception as e:
            logger.error(f"Error pre-fetching token prices: {e}")
        
        # Initialize event monitor if needed (temporarily disabled due to RPC issues)
        # TODO: Re-enable when CDP webhooks are available or RPC session issues are resolved
        # if not self.event_monitor:
        #     from src.blockchain.rpc_reader import RPCReader
        #     from config.settings import settings
        #     # Create event monitor with RPC reader
        #     rpc_reader = RPCReader(settings.cdp_rpc_url)
        #     self.event_monitor = EventMonitor(rpc_reader)
        #     # Start monitoring for known pools
        #     pool_addresses = []
        #     for pair in self._get_pairs_to_scan():
        #         pool_info = await self.base_client.get_pool_info(
        #             pair["token_a"], pair["token_b"], pair["stable"]
        #         )
        #         if pool_info and pool_info.get("address"):
        #             pool_addresses.append(pool_info["address"])
        #     if pool_addresses:
        #         await self.event_monitor.start_monitoring(pool_addresses)
        
        # Get major token pairs to scan
        pairs_to_scan = self._get_pairs_to_scan()
        
        # Scan each pair
        new_opportunities = {
            "high_apr": [],
            "high_volume": [],
            "new_pools": [],
            "imbalanced": [],
        }
        
        for pair in pairs_to_scan:
            pool_data = await self._scan_pool(pair["token_a"], pair["token_b"], pair["stable"])
            
            if pool_data:
                # Categorize opportunity
                await self._categorize_opportunity(pool_data, new_opportunities)
                    
        # Update opportunities
        self.opportunities = new_opportunities
        self.last_scan = datetime.utcnow()
        
        # Store significant findings in memory
        await self._store_findings(new_opportunities)
        
    def _get_pairs_to_scan(self) -> List[Dict]:
        """Get list of pairs to scan."""
        # Focus on major pairs
        major_pairs = [
            {"token_a": "WETH", "token_b": "USDC", "stable": False},
            {"token_a": "WETH", "token_b": "DAI", "stable": False},
            {"token_a": "AERO", "token_b": "USDC", "stable": False},
            {"token_a": "AERO", "token_b": "WETH", "stable": False},
            {"token_a": "USDC", "token_b": "DAI", "stable": True},
            {"token_a": "USDC", "token_b": "USDbC", "stable": True},
        ]
        
        return major_pairs
        
    async def _scan_pool(self, token_a: str, token_b: str, stable: bool) -> Optional[Dict]:
        """Scan a specific pool."""
        try:
            # Get pool info
            pool_info = await self.base_client.get_pool_info(token_a, token_b, stable)
            
            if not pool_info:
                return None
                
            # Calculate real APRs
            pool_address = pool_info.get("address")
            volume_24h = await self._get_real_volume(pool_info)
            total_apr, fee_apr, emission_apr = await self._calculate_real_apr(
                pool_info, pool_address, stable
            )
            
            # Use real data from CDP
            pool_data = {
                "pair": f"{token_a}/{token_b}",
                "address": pool_address,
                "stable": stable,
                "tvl": pool_info.get("tvl", Decimal("0")),
                "volume_24h": volume_24h,
                "apr": total_apr,
                "fee_apr": fee_apr,
                "incentive_apr": emission_apr,
                "reserves": {
                    token_a: pool_info.get("reserve_a", Decimal("0")),
                    token_b: pool_info.get("reserve_b", Decimal("0")),
                },
                "ratio": pool_info.get("ratio", Decimal("1")),
                "imbalanced": pool_info.get("imbalanced", False),
                "timestamp": datetime.utcnow(),
            }
            
            # Store in cache
            pool_key = f"{token_a}/{token_b}-{stable}"
            self.pools[pool_key] = pool_data
            
            logger.debug(f"Scanned pool {pool_key}: address={pool_data.get('address')}, APR={pool_data.get('apr')}%, TVL=${pool_data.get('tvl'):,.0f}")
            
            return pool_data
            
        except Exception as e:
            logger.error(f"Error scanning pool {token_a}/{token_b}: {e}")
            return None
            
    def _calculate_fee_apr(self, volume_24h: Decimal, tvl: Decimal, stable: bool) -> Decimal:
        """Calculate fee APR based on actual volume and TVL."""
        if tvl == 0:
            return Decimal("0")
            
        # Fee rates: 0.01% for stable, 0.3% for volatile
        fee_rate = Decimal("0.0001") if stable else Decimal("0.003")
        
        # Calculate daily fees
        daily_fees = volume_24h * fee_rate
        
        # Annualize and convert to percentage
        annual_fees = daily_fees * Decimal("365")
        fee_apr = (annual_fees / tvl) * Decimal("100")
        
        logger.debug(f"Fee APR calculation: volume=${volume_24h:,.0f}, TVL=${tvl:,.0f}, fee_rate={fee_rate}, APR={fee_apr:.2f}%")
        
        return fee_apr
    
    async def _get_real_volume(self, pool_info: Dict) -> Decimal:
        """Get real 24h volume from event monitor or estimate temporarily."""
        if self.event_monitor and pool_info.get("address"):
            real_volume = self.event_monitor.get_24h_volume(pool_info["address"])
            if real_volume > 0:
                logger.info(f"Real 24h volume for {pool_info['address']}: ${real_volume:,.0f}")
                return real_volume
        
        # Temporary estimation while event monitor is disabled
        # Typical DEX pools have daily volume between 10-50% of TVL
        tvl = pool_info.get("tvl", Decimal("0"))
        if tvl > 0:
            # Conservative estimate: 20% of TVL for active pools
            estimated_volume = tvl * Decimal("0.2")
            logger.debug(f"Estimated volume for {pool_info.get('address', 'unknown')}: ${estimated_volume:,.0f} (20% of TVL)")
            return estimated_volume
        
        return Decimal("0")
    
    async def _calculate_real_apr(self, pool_info: Dict, pool_address: str, stable: bool) -> Tuple[Decimal, Decimal, Decimal]:
        """Calculate real APR from pool data and gauge emissions.
        
        Returns:
            Tuple of (total_apr, fee_apr, emission_apr)
        """
        tvl = pool_info.get("tvl", Decimal("0"))
        if tvl == 0:
            return Decimal("0"), Decimal("0"), Decimal("0")
            
        # Calculate fee APR from actual volume only
        volume_24h = await self._get_real_volume(pool_info)
        fee_apr = self._calculate_fee_apr(volume_24h, tvl, stable)
        
        # Get real emission APR using CDP client
        emission_apr = Decimal("0")
        if pool_address:
            try:
                emission_apr = await self.base_client.calculate_emission_apr(pool_address, tvl)
                if emission_apr > 0:
                    logger.info(f"Real emission APR for {pool_address}: {emission_apr:.2f}%")
            except Exception as e:
                logger.error(f"Failed to get emission APR for {pool_address}: {e}")
        
        total_apr = fee_apr + emission_apr
        
        logger.info(
            f"Pool {pool_address} APR breakdown: "
            f"fee={fee_apr:.2f}%, emission={emission_apr:.2f}%, total={total_apr:.2f}%"
        )
        
        return total_apr, fee_apr, emission_apr
    
    async def _get_real_aero_price(self) -> Decimal:
        """Get real AERO token price from DEX."""
        try:
            # Get AERO/USDC pool info to determine price
            pool_info = await self.base_client.get_pool_info("AERO", "USDC", False)
            if pool_info and pool_info.get("reserve0") and pool_info.get("reserve1"):
                # Assuming AERO is token0 and USDC is token1
                aero_reserve = pool_info["reserve0"]
                usdc_reserve = pool_info["reserve1"]
                
                if aero_reserve > 0:
                    # Price = USDC per AERO
                    aero_price = usdc_reserve / aero_reserve
                    logger.info(f"Real AERO price from DEX: ${aero_price:.4f}")
                    return aero_price
                    
        except Exception as e:
            logger.error(f"Failed to fetch AERO price: {e}")
            
        # If we can't get the price, return 0 (no emissions APR)
        logger.warning("Could not fetch real AERO price - emission APR will be 0")
        return Decimal("0")
            
    async def _categorize_opportunity(self, pool_data: Dict, opportunities: Dict):
        """Categorize pool as an opportunity."""
        # High APR opportunity
        if pool_data["apr"] > Decimal("50"):
            opportunities["high_apr"].append({
                **pool_data,
                "reason": f"High APR: {pool_data['apr']}%",
                "score": float(pool_data["apr"]) / 100,
            })
            
        # High volume opportunity
        if pool_data["volume_24h"] > Decimal("1000000"):
            opportunities["high_volume"].append({
                **pool_data,
                "reason": f"High volume: ${pool_data['volume_24h']:,.0f}",
                "score": float(pool_data["volume_24h"]) / 1000000,
            })
            
        # Check if pool is imbalanced (mock check)
        # TODO: Implement real imbalance detection
        if self._is_imbalanced(pool_data):
            opportunities["imbalanced"].append({
                **pool_data,
                "reason": "Pool imbalanced - arbitrage opportunity",
                "score": 0.8,
            })
            
    def _is_imbalanced(self, pool_data: Dict) -> bool:
        """Check if pool is imbalanced."""
        # Use the imbalanced flag from pool data if available
        if "imbalanced" in pool_data:
            return pool_data["imbalanced"]
            
        # Otherwise check ratio
        ratio = pool_data.get("ratio", Decimal("1"))
        # Consider imbalanced if ratio deviates more than 10% from 1:1
        return abs(ratio - Decimal("1")) > Decimal("0.1")
        
    async def _store_findings(self, opportunities: Dict):
        """Store significant findings in memory - enhanced to capture all significant pools."""
        from config.settings import settings
        
        # Get thresholds from settings or use defaults
        min_apr_for_memory = getattr(settings, 'min_apr_for_memory', 20)
        min_volume_for_memory = getattr(settings, 'min_volume_for_memory', 100000)
        
        # First, store ALL pools that meet basic criteria (not just categorized opportunities)
        # This ensures we don't miss pools with APR between 20-50%
        for pool_key, pool_data in self.pools.items():
            # Store any pool with meaningful APR or volume
            if pool_data.get("apr", 0) >= min_apr_for_memory or pool_data.get("volume_24h", 0) >= min_volume_for_memory:
                # Create consistent observation structure
                observation = {
                    "type": "observation",
                    "category": "pool_analysis",  # Use general category
                    "timestamp": pool_data.get("timestamp", datetime.utcnow()).isoformat() if isinstance(pool_data.get("timestamp"), datetime) else pool_data.get("timestamp"),
                    "confidence": 0.8,
                    "pool": pool_data["pair"],
                    "pool_address": pool_data.get("address"),
                    "tvl": float(pool_data.get("tvl", 0)),
                    "apr": float(pool_data.get("apr", 0)),
                    "fee_apr": float(pool_data.get("fee_apr", 0)),
                    "incentive_apr": float(pool_data.get("incentive_apr", 0)),
                    "volume_24h": float(pool_data.get("volume_24h", 0)),
                    "stable": pool_data.get("stable", False),
                    "imbalanced": pool_data.get("imbalanced", False),
                    "ratio": float(pool_data.get("ratio", 1)),
                    "reserves": {k: float(v) for k, v in pool_data.get("reserves", {}).items()},
                }
                
                await self.memory.remember(
                    content=f"Pool analysis: {pool_data['pair']} - APR: {pool_data.get('apr', 0):.2f}%, Volume: ${pool_data.get('volume_24h', 0):,.0f}, TVL: ${pool_data.get('tvl', 0):,.0f}",
                    memory_type=MemoryType.OBSERVATION,
                    category="pool_analysis",
                    metadata=observation,
                    confidence=observation["confidence"]
                )
                logger.info(f"Stored pool data for {pool_data['pair']} with APR {pool_data.get('apr', 0):.2f}%")
        
        # Store ALL high APR pools, not just the top one
        if opportunities["high_apr"]:
            for pool in opportunities["high_apr"]:
                if pool["apr"] >= min_apr_for_memory:
                    # Create consistent observation structure
                    observation = {
                        "type": "observation",
                        "category": "pool_behavior",
                        "timestamp": pool.get("timestamp", datetime.utcnow()).isoformat() if isinstance(pool.get("timestamp"), datetime) else pool.get("timestamp"),
                        "confidence": 0.9 if pool["apr"] > 50 else 0.7,
                        "pool": pool["pair"],
                        "pool_address": pool.get("address"),
                        "tvl": float(pool["tvl"]),
                        "apr": float(pool["apr"]),
                        "fee_apr": float(pool.get("fee_apr", 0)),
                        "incentive_apr": float(pool.get("incentive_apr", 0)),
                        "stable": pool.get("stable", False),
                        "imbalanced": pool.get("imbalanced", False),
                        "ratio": float(pool.get("ratio", 1)),
                        "reserves": {k: float(v) for k, v in pool.get("reserves", {}).items()},
                    }
                    
                    await self.memory.remember(
                        content=f"High APR pool: {pool['pair']} at {pool['apr']}% APR (TVL: ${pool['tvl']:,.0f})",
                        memory_type=MemoryType.OBSERVATION,
                        category="pool_behavior",
                        metadata=observation,
                        confidence=observation["confidence"]
                    )
            
        # Store ALL high volume pools
        if opportunities["high_volume"]:
            for pool in opportunities["high_volume"]:
                if pool["volume_24h"] >= min_volume_for_memory:
                    # Create consistent observation structure
                    observation = {
                        "type": "observation",
                        "category": "pool_behavior",
                        "timestamp": pool.get("timestamp", datetime.utcnow()).isoformat() if isinstance(pool.get("timestamp"), datetime) else pool.get("timestamp"),
                        "confidence": 0.9 if pool["volume_24h"] > 1000000 else 0.8,
                        "pool": pool["pair"],
                        "pool_address": pool.get("address"),
                        "tvl": float(pool["tvl"]),
                        "volume_24h": float(pool["volume_24h"]),
                        "apr": float(pool["apr"]),
                        "volume_to_tvl_ratio": float(pool["volume_24h"] / pool["tvl"]) if pool["tvl"] > 0 else 0,
                        "stable": pool.get("stable", False),
                        "imbalanced": pool.get("imbalanced", False),
                        "ratio": float(pool.get("ratio", 1)),
                        "reserves": {k: float(v) for k, v in pool.get("reserves", {}).items()},
                    }
                    
                    await self.memory.remember(
                        content=f"High volume pool: {pool['pair']} with ${pool['volume_24h']:,.0f} daily volume (APR: {pool['apr']}%)",
                        memory_type=MemoryType.OBSERVATION,
                        category="pool_behavior",
                        metadata=observation,
                        confidence=observation["confidence"]
                    )
                    
        # Store imbalanced pools for arbitrage tracking
        if opportunities["imbalanced"]:
            for pool in opportunities["imbalanced"]:
                # Only store significantly imbalanced pools
                if pool.get("ratio") and (pool["ratio"] > 2 or pool["ratio"] < 0.5):
                    # Create consistent observation structure
                    observation = {
                        "type": "observation",
                        "category": "arbitrage_opportunity",
                        "timestamp": pool.get("timestamp", datetime.utcnow()).isoformat() if isinstance(pool.get("timestamp"), datetime) else pool.get("timestamp"),
                        "confidence": 0.8,
                        "pool": pool["pair"],
                        "pool_address": pool.get("address"),
                        "tvl": float(pool["tvl"]),
                        "ratio": float(pool["ratio"]),
                        "stable": pool.get("stable", False),
                        "imbalanced": True,
                        "reserves": {k: float(v) for k, v in pool.get("reserves", {}).items()},
                    }
                    
                    await self.memory.remember(
                        content=f"Imbalanced pool detected: {pool['pair']} with ratio {pool['ratio']:.4f}",
                        memory_type=MemoryType.OBSERVATION,
                        category="arbitrage_opportunity",
                        metadata=observation,
                        confidence=0.8
                    )
                    
        # Store new pools if any
        if opportunities.get("new_pools"):
            for pool in opportunities["new_pools"]:
                await self.memory.remember(
                    content=f"New pool discovered: {pool['pair']} (TVL: ${pool['tvl']:,.0f}, APR: {pool['apr']}%)",
                    memory_type=MemoryType.OBSERVATION,
                    category="new_pool",
                    metadata={
                        "pool": pool["pair"],
                        "pool_address": pool.get("address"),
                        "apr": float(pool["apr"]),
                        "tvl": float(pool["tvl"]),
                        "stable": pool.get("stable", False),
                        "timestamp": pool.get("timestamp"),
                    },
                    confidence=1.0
                )
            
    def get_opportunities(self, category: Optional[str] = None) -> List[Dict]:
        """Get current opportunities."""
        if category:
            return self.opportunities.get(category, [])
            
        # Return all opportunities sorted by score
        all_opps = []
        for opps in self.opportunities.values():
            all_opps.extend(opps)
            
        return sorted(all_opps, key=lambda x: x.get("score", 0), reverse=True)
        
    def get_pool_data(self, token_a: str, token_b: str, stable: bool = False) -> Optional[Dict]:
        """Get cached pool data."""
        pool_key = f"{token_a}/{token_b}-{stable}"
        return self.pools.get(pool_key)
        
    def get_summary(self) -> Dict:
        """Get scanning summary."""
        return {
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "pools_tracked": len(self.pools),
            "opportunities": {
                "high_apr": len(self.opportunities["high_apr"]),
                "high_volume": len(self.opportunities["high_volume"]),
                "new_pools": len(self.opportunities["new_pools"]),
                "imbalanced": len(self.opportunities["imbalanced"]),
            },
            "top_apr": max(
                (p["apr"] for p in self.pools.values()),
                default=Decimal("0")
            ),
            "total_tvl": sum(
                p["tvl"] for p in self.pools.values()
            ),
        }