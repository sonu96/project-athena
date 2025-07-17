"""
Cloud Function to collect Aerodrome pool data using CDP toolkit

Uses CDP RPC endpoint to avoid rate limiting.
"""

import functions_framework
import json
import os
from datetime import datetime
from google.cloud import bigquery
import logging
import asyncio

# Import local CDP wrapper
from cdp_wrapper import SimpleCDPClient, AerodromeCDP

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('GCP_PROJECT', 'athena-defi-agent-1752635199')
DATASET_ID = os.environ.get('BIGQUERY_DATASET', 'athena_analytics')
TABLE_ID = 'pool_observations'

# Common tokens for identification
KNOWN_TOKENS = {
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": "USDC",
    "0x4200000000000000000000000000000000000006": "WETH",
    "0x940181a94A35A4569E4529A3CDfB74e38FD98631": "AERO",
    "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb": "DAI",
    "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA": "USDbC",
}

# Pool data collector using CDP
class CDPPoolCollector:
    def __init__(self):
        self.cdp_client = None
        self.aerodrome = None
        
    async def initialize(self):
        """Initialize CDP client and Aerodrome integration"""
        try:
            # Create CDP client instance
            self.cdp_client = SimpleCDPClient()
            
            # Initialize connection
            if not self.cdp_client.initialize():
                logger.error("Failed to initialize CDP connection")
                return False
            
            # Create Aerodrome integration
            self.aerodrome = AerodromeCDP(self.cdp_client)
            
            logger.info("CDP and Aerodrome integration initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    async def get_token_info(self, token_address: str):
        """Get token symbol using known tokens mapping"""
        # For now, use known tokens to avoid extra CDP calls
        symbol = KNOWN_TOKENS.get(token_address, "???")
        decimals = 18  # Most tokens use 18 decimals
        return symbol, decimals
    
    def estimate_tvl_usd(self, reserves, token0_symbol, token1_symbol, decimals0=18, decimals1=18):
        """Simple TVL estimation"""
        # Convert reserves to human readable
        reserve0 = reserves[0] / (10 ** decimals0)
        reserve1 = reserves[1] / (10 ** decimals1)
        
        # Simple estimation based on stablecoins
        if token0_symbol in ["USDC", "DAI", "USDbC"]:
            return reserve0 * 2
        elif token1_symbol in ["USDC", "DAI", "USDbC"]:
            return reserve1 * 2
        elif token0_symbol == "WETH":
            # Rough ETH price estimate
            return reserve0 * 3000 * 2
        elif token1_symbol == "WETH":
            return reserve1 * 3000 * 2
        else:
            # Unknown pair - return placeholder
            return 100000
    
    async def collect_pool_data(self, pool_address: str):
        """Collect data for a single pool using CDP"""
        try:
            # Get pool data using CDP
            pool_data = await self.aerodrome.get_pool_data(pool_address)
            
            if not pool_data:
                return None
            
            # Get token symbols
            token0_symbol, decimals0 = await self.get_token_info(pool_data['token0'])
            token1_symbol, decimals1 = await self.get_token_info(pool_data['token1'])
            
            # Get stable flag
            is_stable = pool_data.get('is_stable', False)
            
            # Estimate TVL
            tvl_usd = self.estimate_tvl_usd(
                [pool_data['reserve0'], pool_data['reserve1']], 
                token0_symbol, 
                token1_symbol,
                decimals0,
                decimals1
            )
            
            # Estimate volume (simplified - 10% of TVL as daily volume)
            volume_24h_usd = tvl_usd * 0.1
            
            # Calculate simple APY estimates
            fee_tier = 0.0005 if is_stable else 0.003
            fee_apy = (volume_24h_usd * fee_tier * 365) / tvl_usd if tvl_usd > 0 else 0
            reward_apy = 0.05  # Placeholder
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": "pool-collector-cdp",
                "pool_address": pool_address,
                "pool_type": "STABLE" if is_stable else "VOLATILE",
                "token0_symbol": token0_symbol,
                "token1_symbol": token1_symbol,
                "tvl_usd": tvl_usd,
                "volume_24h_usd": volume_24h_usd,
                "fee_apy": fee_apy,
                "reward_apy": reward_apy,
                "total_apy": fee_apy + reward_apy,
                "reserve0": float(pool_data['reserve0']),
                "reserve1": float(pool_data['reserve1']),
                "lp_supply": float(pool_data.get('total_supply', 0))
            }
            
        except Exception as e:
            logger.error(f"Error collecting pool {pool_address}: {e}")
            return None
    
    async def collect_pools(self):
        """Main collection logic using CDP"""
        logger.info("Starting CDP-based Aerodrome pool collection")
        
        if not await self.initialize():
            return {"error": "Failed to initialize CDP"}, 500
        
        try:
            # Get total pools using CDP
            pool_count = await self.aerodrome.get_pool_count()
            
            if not pool_count:
                logger.warning("Could not get pool count from CDP")
                return {"error": "Failed to get pool count"}, 500
                
            logger.info(f"Total Aerodrome pools: {pool_count}")
            
            # Collect data from recent pools (last 20)
            pools_to_check = min(20, pool_count)
            start_idx = max(0, pool_count - pools_to_check)
            
            collected_data = []
            
            # Process pools one by one to avoid overwhelming CDP
            for i in range(start_idx, pool_count):
                try:
                    # Get pool address using CDP
                    pool_address = await self.aerodrome.get_pool_address(i)
                    
                    if not pool_address:
                        continue
                    
                    # Collect pool data using CDP
                    pool_data = await self.collect_pool_data(pool_address)
                    
                    if pool_data and pool_data["tvl_usd"] > 10000:  # Min $10k TVL
                        collected_data.append(pool_data)
                        logger.info(f"Collected pool {pool_data['token0_symbol']}/{pool_data['token1_symbol']} - TVL: ${pool_data['tvl_usd']:,.0f}")
                    
                    # Small delay between pools
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error with pool index {i}: {e}")
                    continue
            
            logger.info(f"Collected {len(collected_data)} pools with >$10k TVL using CDP")
            
            # Store in BigQuery
            if collected_data:
                client = bigquery.Client(project=PROJECT_ID)
                table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
                
                errors = client.insert_rows_json(table_id, collected_data)
                
                if errors:
                    logger.error(f"BigQuery insert errors: {errors}")
                    return {
                        "error": "Failed to insert data",
                        "details": errors
                    }, 500
                
                logger.info(f"Successfully inserted {len(collected_data)} rows to BigQuery")
            
            return {
                "success": True,
                "pools_collected": len(collected_data),
                "timestamp": datetime.utcnow().isoformat(),
                "method": "CDP Toolkit"
            }, 200
            
        except Exception as e:
            logger.error(f"CDP collection error: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }, 500


# Async wrapper for cloud function
def run_async_collection():
    """Run the async collection in sync context"""
    collector = CDPPoolCollector()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result, status_code = loop.run_until_complete(collector.collect_pools())
        return result, status_code
    finally:
        loop.close()


@functions_framework.http
def collect_pools(request):
    """Cloud Function entry point"""
    
    result, status_code = run_async_collection()
    return json.dumps(result), status_code


# For local testing
if __name__ == "__main__":
    print("Testing CDP pool collector locally...")
    result, status = run_async_collection()
    print(json.dumps(result, indent=2))