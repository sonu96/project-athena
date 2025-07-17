"""
Cloud Function to collect Aerodrome pool data using CDP AgentKit

Uses CDP to avoid rate limiting and properly integrate with BASE mainnet.
"""

import functions_framework
import json
import os
import asyncio
from datetime import datetime
from google.cloud import bigquery
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('GCP_PROJECT', 'athena-defi-agent-1752635199')
DATASET_ID = os.environ.get('BIGQUERY_DATASET', 'athena_analytics')
TABLE_ID = 'pool_observations'

# Import CDP client
try:
    from cdp import Wallet, Cdp
    CDP_AVAILABLE = True
except ImportError:
    logger.error("CDP SDK not available!")
    CDP_AVAILABLE = False

# Aerodrome contracts on BASE mainnet
AERODROME_FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"

# Common tokens for identification
KNOWN_TOKENS = {
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": "USDC",
    "0x4200000000000000000000000000000000000006": "WETH",
    "0x940181a94A35A4569E4529A3CDfB74e38FD98631": "AERO",
    "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb": "DAI",
    "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA": "USDbC",
}

# Minimal ABIs
FACTORY_ABI = {
    "allPoolsLength": {
        "inputs": [],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    "allPools": {
        "inputs": [{"type": "uint256", "name": "index"}],
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
}

POOL_ABI = {
    "token0": {
        "inputs": [],
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    "token1": {
        "inputs": [],
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    "getReserves": {
        "inputs": [],
        "outputs": [
            {"type": "uint256", "name": "_reserve0"},
            {"type": "uint256", "name": "_reserve1"},
            {"type": "uint256", "name": "_blockTimestampLast"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    "stable": {
        "inputs": [],
        "outputs": [{"type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    "totalSupply": {
        "inputs": [],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
}

ERC20_ABI = {
    "symbol": {
        "inputs": [],
        "outputs": [{"type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    "decimals": {
        "inputs": [],
        "outputs": [{"type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
}


class CDPPoolCollector:
    """Collect pool data using CDP AgentKit"""
    
    def __init__(self):
        self.wallet = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize CDP connection"""
        if not CDP_AVAILABLE:
            logger.error("CDP SDK not available - cannot collect data")
            return False
            
        try:
            # Configure CDP
            Cdp.configure(
                api_key_name=os.environ.get('CDP_API_KEY_NAME'),
                api_key_private_key=os.environ.get('CDP_API_KEY_SECRET')
            )
            
            # Create or load wallet
            wallet_data = os.environ.get('CDP_WALLET_DATA')
            if wallet_data:
                # Load existing wallet
                self.wallet = Wallet.import_data(wallet_data)
            else:
                # Create new wallet on BASE
                self.wallet = Wallet.create(network_id="base-mainnet")
                logger.info(f"Created new CDP wallet: {self.wallet.default_address}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize CDP: {e}")
            return False
    
    async def read_contract(self, contract_address: str, method: str, abi: dict, args: list = None):
        """Read data from contract using CDP"""
        try:
            result = await self.wallet.read_contract(
                contract_address=contract_address,
                method=method,
                abi=json.dumps([abi]),
                args=args or []
            )
            return result
        except Exception as e:
            logger.error(f"Error reading {method} from {contract_address}: {e}")
            raise
    
    async def get_token_info(self, token_address: str):
        """Get token symbol and decimals"""
        try:
            # Try to get symbol
            try:
                symbol = await self.read_contract(
                    token_address, 
                    "symbol", 
                    ERC20_ABI["symbol"]
                )
            except:
                symbol = KNOWN_TOKENS.get(token_address, "???")
            
            # Try to get decimals
            try:
                decimals = await self.read_contract(
                    token_address,
                    "decimals", 
                    ERC20_ABI["decimals"]
                )
            except:
                decimals = 18
                
            return symbol, decimals
            
        except Exception as e:
            logger.error(f"Error getting token info for {token_address}: {e}")
            return KNOWN_TOKENS.get(token_address, "???"), 18
    
    def estimate_tvl_usd(self, reserves, token0_symbol, token1_symbol, decimals0, decimals1):
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
            # Get pool data in parallel where possible
            token0_task = self.read_contract(pool_address, "token0", POOL_ABI["token0"])
            token1_task = self.read_contract(pool_address, "token1", POOL_ABI["token1"])
            reserves_task = self.read_contract(pool_address, "getReserves", POOL_ABI["getReserves"])
            stable_task = self.read_contract(pool_address, "stable", POOL_ABI["stable"])
            supply_task = self.read_contract(pool_address, "totalSupply", POOL_ABI["totalSupply"])
            
            # Wait for all tasks
            token0 = await token0_task
            token1 = await token1_task
            reserves = await reserves_task
            is_stable = await stable_task
            total_supply = await supply_task
            
            # Get token info
            token0_symbol, decimals0 = await self.get_token_info(token0)
            token1_symbol, decimals1 = await self.get_token_info(token1)
            
            # Estimate TVL
            tvl_usd = self.estimate_tvl_usd(
                reserves, 
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
            reward_apy = 0.05  # Placeholder - would need gauge data
            
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
                "reserve0": float(reserves[0]),
                "reserve1": float(reserves[1]),
                "lp_supply": float(total_supply)
            }
            
        except Exception as e:
            logger.error(f"Error collecting pool {pool_address}: {e}")
            return None
    
    async def collect_pools(self):
        """Main collection logic"""
        logger.info("Starting CDP-based Aerodrome pool collection")
        
        if not self.initialized:
            if not await self.initialize():
                return {"error": "Failed to initialize CDP"}, 500
        
        try:
            # Get total pools from factory
            pool_count = await self.read_contract(
                AERODROME_FACTORY,
                "allPoolsLength",
                FACTORY_ABI["allPoolsLength"]
            )
            
            pool_count = int(pool_count)
            logger.info(f"Total Aerodrome pools: {pool_count}")
            
            # Collect data from recent pools (last 20)
            pools_to_check = min(20, pool_count)
            start_idx = max(0, pool_count - pools_to_check)
            
            collected_data = []
            
            # Process pools in batches to avoid overwhelming CDP
            batch_size = 5
            for batch_start in range(start_idx, pool_count, batch_size):
                batch_end = min(batch_start + batch_size, pool_count)
                
                # Get pool addresses for this batch
                pool_tasks = []
                for i in range(batch_start, batch_end):
                    task = self.read_contract(
                        AERODROME_FACTORY,
                        "allPools",
                        FACTORY_ABI["allPools"],
                        [i]
                    )
                    pool_tasks.append(task)
                
                # Wait for pool addresses
                pool_addresses = await asyncio.gather(*pool_tasks, return_exceptions=True)
                
                # Collect data for each pool
                for pool_address in pool_addresses:
                    if isinstance(pool_address, Exception):
                        continue
                        
                    pool_data = await self.collect_pool_data(pool_address)
                    
                    if pool_data and pool_data["tvl_usd"] > 10000:  # Min $10k TVL
                        collected_data.append(pool_data)
                        logger.info(f"Collected pool {pool_data['token0_symbol']}/{pool_data['token1_symbol']} - TVL: ${pool_data['tvl_usd']:,.0f}")
                
                # Small delay between batches
                await asyncio.sleep(1)
            
            logger.info(f"Collected {len(collected_data)} pools with >$10k TVL")
            
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
                "method": "CDP"
            }, 200
            
        except Exception as e:
            logger.error(f"CDP collection error: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }, 500


# Global collector instance
collector = CDPPoolCollector()


@functions_framework.http
async def collect_pools(request):
    """Cloud Function entry point"""
    result, status_code = await collector.collect_pools()
    return json.dumps(result), status_code


# For local testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        result, status = await collector.collect_pools()
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())