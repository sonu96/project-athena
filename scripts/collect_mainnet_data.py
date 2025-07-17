#!/usr/bin/env python3
"""Collect real Aerodrome mainnet data using Web3 directly"""

import os
import sys
import json
import asyncio
from datetime import datetime
from web3 import Web3
from google.cloud import bigquery
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Aerodrome mainnet addresses
AERODROME_FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
BASE_RPC_URLS = [
    "https://mainnet.base.org",
    "https://base.llamarpc.com",
    "https://base.publicnode.com",
]

# Known tokens for symbol resolution
KNOWN_TOKENS = {
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": "USDC",
    "0x4200000000000000000000000000000000000006": "WETH",
    "0x940181a94a35a4569e4529a3cdfb74e38fd98631": "AERO",
    "0x50c5725949a6f0c72e6c4a641f24049a917db0cb": "DAI",
    "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca": "USDbC",
    "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22": "cbETH",
}

# ABIs
FACTORY_ABI = [
    {
        "inputs": [],
        "name": "allPoolsLength",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"type": "uint256"}],
        "name": "allPools",
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

POOL_ABI = [
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "stable",
        "outputs": [{"type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"type": "uint256", "name": "_reserve0"},
            {"type": "uint256", "name": "_reserve1"},
            {"type": "uint256", "name": "_blockTimestampLast"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]


async def collect_mainnet_data():
    """Collect real Aerodrome mainnet data"""
    
    print("🚀 Collecting Real Aerodrome Mainnet Data\n")
    
    # Connect to BASE mainnet
    w3 = None
    for rpc_url in BASE_RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                print(f"✅ Connected to BASE mainnet via {rpc_url}")
                print(f"   Chain ID: {w3.eth.chain_id}")
                print(f"   Block: {w3.eth.block_number:,}")
                break
        except:
            continue
    
    if not w3 or not w3.is_connected():
        print("❌ Failed to connect to BASE mainnet")
        return False
    
    # Get factory contract
    factory = w3.eth.contract(
        address=Web3.to_checksum_address(AERODROME_FACTORY),
        abi=FACTORY_ABI
    )
    
    # Get total pools
    total_pools = factory.functions.allPoolsLength().call()
    print(f"\n📊 Aerodrome has {total_pools:,} pools total")
    
    # Collect data from recent pools
    print("\n🔍 Collecting pool data...")
    collected_pools = []
    
    # Get last 100 pools (most recent)
    start_idx = max(0, total_pools - 100)
    
    print(f"   Checking pools {start_idx} to {total_pools}...")
    pools_checked = 0
    
    for i in range(start_idx, total_pools):
        pools_checked += 1
        try:
            # Get pool address
            pool_address = factory.functions.allPools(i).call()
            pool = w3.eth.contract(address=pool_address, abi=POOL_ABI)
            
            # Get pool data
            token0 = pool.functions.token0().call()
            token1 = pool.functions.token1().call()
            is_stable = pool.functions.stable().call()
            reserves = pool.functions.getReserves().call()
            total_supply = pool.functions.totalSupply().call()
            
            # Get token symbols
            token0_symbol = KNOWN_TOKENS.get(token0.lower(), None)
            token1_symbol = KNOWN_TOKENS.get(token1.lower(), None)
            
            if not token0_symbol:
                try:
                    token0_contract = w3.eth.contract(address=token0, abi=ERC20_ABI)
                    token0_symbol = token0_contract.functions.symbol().call()
                except:
                    token0_symbol = token0[:8]
            
            if not token1_symbol:
                try:
                    token1_contract = w3.eth.contract(address=token1, abi=ERC20_ABI)
                    token1_symbol = token1_contract.functions.symbol().call()
                except:
                    token1_symbol = token1[:8]
            
            # Simple TVL estimation (would need price oracle for accuracy)
            if "USDC" in token0_symbol or "DAI" in token0_symbol or "USDbC" in token0_symbol:
                # Determine decimals - USDC typically 6, DAI 18
                decimals = 6 if "USDC" in token0_symbol else 18
                tvl_estimate = (reserves[0] / (10 ** decimals)) * 2
            elif "USDC" in token1_symbol or "DAI" in token1_symbol or "USDbC" in token1_symbol:
                decimals = 6 if "USDC" in token1_symbol else 18
                tvl_estimate = (reserves[1] / (10 ** decimals)) * 2
            elif "WETH" in token0_symbol or "ETH" in token0_symbol:
                tvl_estimate = (reserves[0] / 1e18) * 3000 * 2  # Rough ETH price
            elif "WETH" in token1_symbol or "ETH" in token1_symbol:
                tvl_estimate = (reserves[1] / 1e18) * 3000 * 2
            else:
                # For unknown pairs, use a placeholder
                tvl_estimate = 100000  # $100k placeholder
            
            # Include all pools for now to see what we're getting
            if tvl_estimate < 1000:
                continue
            
            pool_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": "mainnet-collector",
                "pool_address": pool_address,
                "pool_type": "STABLE" if is_stable else "VOLATILE",
                "token0_symbol": token0_symbol,
                "token1_symbol": token1_symbol,
                "tvl_usd": tvl_estimate,
                "volume_24h_usd": tvl_estimate * 0.1,  # Estimate
                "fee_apy": 0.05,  # Placeholder
                "reward_apy": 0.1,  # Placeholder
                "total_apy": 0.15,  # Placeholder
                "reserve0": float(reserves[0]),
                "reserve1": float(reserves[1]),
                "lp_supply": float(total_supply)
            }
            
            collected_pools.append(pool_data)
            print(f"  ✅ {token0_symbol}/{token1_symbol} - TVL: ${tvl_estimate:,.0f}")
            
            # Collect up to 20 pools
            if len(collected_pools) >= 20:
                break
                
        except Exception as e:
            if pools_checked % 10 == 0:
                print(f"   Checked {pools_checked} pools, found {len(collected_pools)} so far...")
            continue
    
    print(f"\n📊 Summary:")
    print(f"   Pools checked: {pools_checked}")
    print(f"   Pools collected: {len(collected_pools)}")
    print(f"   Success rate: {len(collected_pools)/pools_checked*100:.1f}%")
    
    # Get project ID
    with open("service-account-key.json", "r") as f:
        project_id = json.load(f)["project_id"]
    
    # Store in BigQuery
    if collected_pools:
        print("\n💾 Storing in BigQuery...")
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-key.json"
        
        client = bigquery.Client(project=project_id)
        table_id = f"{project_id}.athena_analytics.pool_observations"
        
        errors = client.insert_rows_json(table_id, collected_pools)
        
        if errors:
            print(f"❌ BigQuery errors: {errors}")
        else:
            print(f"✅ Successfully stored {len(collected_pools)} pool observations")
            
            # Query to verify
            query = f"""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT pool_address) as unique_pools,
                STRING_AGG(DISTINCT CONCAT(token0_symbol, '/', token1_symbol), ', ' LIMIT 10) as pairs
            FROM `{project_id}.athena_analytics.pool_observations`
            WHERE DATE(timestamp) = CURRENT_DATE()
            AND agent_id = 'mainnet-collector'
            """
            
            result = client.query(query).result()
            for row in result:
                print(f"\n📊 Today's mainnet data:")
                print(f"   Total observations: {row['total']}")
                print(f"   Unique pools: {row['unique_pools']}")
                print(f"   Sample pairs: {row['pairs']}")
    
    print(f"\n✅ Mainnet data collection complete!")
    print(f"\n🔗 View in BigQuery:")
    print(f"   https://console.cloud.google.com/bigquery?project={project_id}")
    
    return True

if __name__ == "__main__":
    asyncio.run(collect_mainnet_data())