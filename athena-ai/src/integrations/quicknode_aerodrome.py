"""
QuickNode Aerodrome API Integration

Simplified interface to Aerodrome DEX using QuickNode's API.
Replaces complex on-chain data collection with reliable API calls.
"""
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import asyncio

from config.settings import settings

logger = logging.getLogger(__name__)


class AerodromeAPI:
    """
    QuickNode Aerodrome API client for simplified DEX interactions.
    
    This replaces hundreds of lines of complex blockchain code with
    simple API calls that provide real-time, accurate data.
    """
    
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        """Initialize the Aerodrome API client."""
        self.api_key = api_key or settings.quicknode_api_key
        self.endpoint = endpoint or settings.quicknode_endpoint
        
        if not self.endpoint:
            # Default QuickNode Base endpoint
            self.endpoint = "https://base-mainnet.g.alchemy.com/v2/"  # Will be replaced with actual QuickNode endpoint
            
        self.base_url = f"{self.endpoint}/addon/aerodrome/v1"
        self.session = None
        
        # Cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = 30  # 30 seconds cache
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an authenticated request to the API."""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, headers=headers, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    raise Exception(f"API request failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
            
    async def get_pools(self, 
                       token0: Optional[str] = None,
                       token1: Optional[str] = None,
                       min_tvl: Optional[float] = None,
                       sort_by: str = "apr") -> List[Dict]:
        """
        Get pool data with optional filters.
        
        Args:
            token0: Filter by token0 address
            token1: Filter by token1 address  
            min_tvl: Minimum TVL filter
            sort_by: Sort field (apr, tvl, volume)
            
        Returns:
            List of pool data dictionaries
        """
        params = {}
        if token0:
            params["token0"] = token0
        if token1:
            params["token1"] = token1
        if min_tvl:
            params["minTvl"] = min_tvl
        params["sortBy"] = sort_by
        
        data = await self._request("GET", "/pools", params=params)
        
        # Transform to our expected format
        pools = []
        for pool in data.get("pools", []):
            pools.append({
                "address": pool["address"],
                "pair": f"{pool['token0Symbol']}/{pool['token1Symbol']}",
                "token0": pool["token0"],
                "token1": pool["token1"],
                "stable": pool["stable"],
                "tvl": Decimal(str(pool["tvlUSD"])),
                "volume_24h": Decimal(str(pool["volume24hUSD"])),
                "apr": Decimal(str(pool["apr"])),
                "fee_apr": Decimal(str(pool["feeApr"])),
                "incentive_apr": Decimal(str(pool["incentiveApr"])),
                "reserves": {
                    pool["token0Symbol"]: Decimal(str(pool["reserve0"])),
                    pool["token1Symbol"]: Decimal(str(pool["reserve1"]))
                },
                "ratio": Decimal(str(pool["reserve1"])) / Decimal(str(pool["reserve0"])) if Decimal(str(pool["reserve0"])) > 0 else Decimal("0"),
                "gauge": pool.get("gauge"),
                "emissions": Decimal(str(pool.get("emissionsUSD", "0")))
            })
            
        return pools
        
    async def get_pool_analytics(self, pool_address: str) -> Dict:
        """
        Get detailed analytics for a specific pool.
        
        Args:
            pool_address: The pool contract address
            
        Returns:
            Detailed pool analytics including historical data
        """
        data = await self._request("GET", f"/pools/{pool_address}/analytics")
        
        return {
            "current": {
                "tvl": Decimal(str(data["current"]["tvlUSD"])),
                "volume_24h": Decimal(str(data["current"]["volume24hUSD"])),
                "apr": Decimal(str(data["current"]["apr"])),
                "fee_apr": Decimal(str(data["current"]["feeApr"])),
                "incentive_apr": Decimal(str(data["current"]["incentiveApr"]))
            },
            "history": {
                "tvl_7d": [Decimal(str(x)) for x in data["history"]["tvl7d"]],
                "volume_7d": [Decimal(str(x)) for x in data["history"]["volume7d"]],
                "apr_7d": [Decimal(str(x)) for x in data["history"]["apr7d"]]
            },
            "predictions": {
                "apr_trend": data.get("predictions", {}).get("aprTrend", "stable"),
                "tvl_growth": data.get("predictions", {}).get("tvlGrowth", 0)
            }
        }
        
    async def get_swap_quote(self,
                           token_in: str,
                           token_out: str, 
                           amount_in: Decimal,
                           slippage: float = 0.5) -> Dict:
        """
        Get optimal swap quote with routing.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount to swap
            slippage: Slippage tolerance in percent
            
        Returns:
            Swap quote with optimal route
        """
        data = await self._request("POST", "/swap/quote", json={
            "tokenIn": token_in,
            "tokenOut": token_out,
            "amountIn": str(amount_in),
            "slippage": slippage
        })
        
        return {
            "amount_out": Decimal(str(data["amountOut"])),
            "amount_out_min": Decimal(str(data["amountOutMin"])),
            "price_impact": Decimal(str(data["priceImpact"])),
            "route": data["route"],
            "gas_estimate": int(data["gasEstimate"]),
            "execution_price": Decimal(str(data["executionPrice"]))
        }
        
    async def build_swap_transaction(self, quote: Dict, recipient: str) -> Dict:
        """
        Build a swap transaction from a quote.
        
        Args:
            quote: Quote from get_swap_quote
            recipient: Recipient address
            
        Returns:
            Transaction data ready to sign and send
        """
        data = await self._request("POST", "/swap/build", json={
            "quote": quote,
            "recipient": recipient
        })
        
        return {
            "to": data["to"],
            "data": data["data"],
            "value": data["value"],
            "gas_limit": int(data["gasLimit"])
        }
        
    async def get_token_prices(self, token_addresses: List[str]) -> Dict[str, Decimal]:
        """
        Get current USD prices for multiple tokens.
        
        Args:
            token_addresses: List of token addresses
            
        Returns:
            Dict mapping token address to USD price
        """
        data = await self._request("POST", "/tokens/prices", json={
            "addresses": token_addresses
        })
        
        return {
            addr: Decimal(str(price)) 
            for addr, price in data["prices"].items()
        }
        
    async def search_opportunities(self,
                                 min_apr: float = 20,
                                 min_tvl: float = 100000,
                                 stable_only: bool = False) -> List[Dict]:
        """
        Search for high-yield opportunities.
        
        Args:
            min_apr: Minimum APR threshold
            min_tvl: Minimum TVL threshold
            stable_only: Only show stable pools
            
        Returns:
            List of opportunity pools sorted by APR
        """
        pools = await self.get_pools(min_tvl=min_tvl, sort_by="apr")
        
        opportunities = []
        for pool in pools:
            if pool["apr"] >= min_apr:
                if not stable_only or pool["stable"]:
                    opportunities.append({
                        **pool,
                        "opportunity_score": float(pool["apr"]) * (1 + min(pool["tvl"] / 1000000, 1))
                    })
                    
        return sorted(opportunities, key=lambda x: x["opportunity_score"], reverse=True)
        
    async def get_rebalance_opportunities(self, 
                                        current_positions: List[Dict],
                                        min_improvement: float = 10) -> List[Dict]:
        """
        Find rebalancing opportunities for current positions.
        
        Args:
            current_positions: List of current position dicts with 'pool' and 'apr'
            min_improvement: Minimum APR improvement percentage
            
        Returns:
            List of rebalancing suggestions
        """
        # Get all pools
        all_pools = await self.get_pools(min_tvl=50000)
        
        suggestions = []
        for position in current_positions:
            current_apr = position["apr"]
            
            # Find better pools
            for pool in all_pools:
                apr_improvement = float(pool["apr"] - current_apr)
                
                if apr_improvement >= min_improvement:
                    suggestions.append({
                        "from_pool": position["pool"],
                        "to_pool": pool["pair"],
                        "current_apr": float(current_apr),
                        "new_apr": float(pool["apr"]),
                        "apr_improvement": apr_improvement,
                        "to_pool_data": pool
                    })
                    
        return sorted(suggestions, key=lambda x: x["apr_improvement"], reverse=True)
        
    async def estimate_compound_roi(self,
                                  pool_address: str,
                                  pending_rewards: Decimal,
                                  gas_price: Decimal) -> Dict:
        """
        Estimate ROI for compounding rewards.
        
        Args:
            pool_address: Pool to compound into
            pending_rewards: Amount of pending rewards
            gas_price: Current gas price in gwei
            
        Returns:
            ROI analysis for compounding
        """
        # Get pool data
        pools = await self.get_pools()
        pool = next((p for p in pools if p["address"] == pool_address), None)
        
        if not pool:
            return {"profitable": False, "reason": "Pool not found"}
            
        # Estimate gas cost (compound typically uses ~200k gas)
        gas_cost_usd = (gas_price * 200000 / 10**9) * 2300  # Assume ETH = $2300
        
        # Calculate daily earnings from compounded rewards
        daily_earnings = pending_rewards * pool["apr"] / 36500
        
        # Days to break even
        breakeven_days = float(gas_cost_usd / daily_earnings) if daily_earnings > 0 else 999
        
        return {
            "profitable": breakeven_days < 7,  # Profitable if break even within a week
            "gas_cost_usd": float(gas_cost_usd),
            "daily_earnings": float(daily_earnings),
            "breakeven_days": breakeven_days,
            "recommendation": "compound" if breakeven_days < 7 else "wait"
        }


# Convenience function for quick testing
async def test_api():
    """Test the Aerodrome API integration."""
    async with AerodromeAPI() as api:
        # Get top pools
        pools = await api.search_opportunities(min_apr=30, min_tvl=500000)
        
        print(f"Found {len(pools)} high-yield opportunities:")
        for pool in pools[:5]:
            print(f"  {pool['pair']}: {pool['apr']}% APR, ${pool['tvl']:,.0f} TVL")
            
        # Get swap quote
        if pools:
            # Example: Quote for swapping 100 USDC to WETH
            quote = await api.get_swap_quote(
                token_in="0x...",  # USDC address
                token_out="0x...",  # WETH address
                amount_in=Decimal("100")
            )
            print(f"\nSwap quote: 100 USDC -> {quote['amount_out']} WETH")
            print(f"Price impact: {quote['price_impact']}%")


if __name__ == "__main__":
    asyncio.run(test_api())