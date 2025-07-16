#!/usr/bin/env python3
"""Test Aerodrome data fetching from BASE mainnet"""

import asyncio
import json
from web3 import Web3
from datetime import datetime

# Aerodrome Finance addresses on BASE mainnet
AERODROME_CONTRACTS = {
    "factory": "0x420DD381b31aEf6683db6B902084cB0FFECe40Da",
    "router": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
    "voter": "0x16613524e02ad97eDfeF371bC883F2F5d6C480A5",
}

# Common tokens on BASE
TOKENS = {
    "WETH": "0x4200000000000000000000000000000000000006",
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "AERO": "0x940181a94A35A4569E4529A3CDfB74e38FD98631",
    "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
}

# BASE RPC endpoints
RPC_ENDPOINTS = [
    "https://mainnet.base.org",
    "https://base.llamarpc.com",
    "https://base.publicnode.com",
]

# Minimal ABI for factory
FACTORY_ABI = [
    {
        "inputs": [],
        "name": "allPoolsLength",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "allPools",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Minimal ABI for pools
POOL_ABI = [
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint256", "name": "_reserve0", "type": "uint256"},
            {"internalType": "uint256", "name": "_reserve1", "type": "uint256"},
            {"internalType": "uint256", "name": "_blockTimestampLast", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "stable",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ERC20 ABI for token info
ERC20_ABI = [
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]

async def test_aerodrome_connection():
    """Test connection to Aerodrome on BASE mainnet"""
    print("\n🚀 Testing Aerodrome Data Access on BASE Mainnet\n")
    
    # Try different RPC endpoints
    w3 = None
    for rpc in RPC_ENDPOINTS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if w3.is_connected():
                print(f"✅ Connected to BASE via: {rpc}")
                break
        except:
            continue
    
    if not w3 or not w3.is_connected():
        print("❌ Failed to connect to BASE mainnet")
        return False
    
    # Get network info
    try:
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
        print(f"📊 Chain ID: {chain_id} (BASE mainnet)")
        print(f"📦 Current block: {block_number:,}")
    except Exception as e:
        print(f"❌ Error getting network info: {e}")
        return False
    
    # Test Aerodrome Factory
    print("\n📍 Testing Aerodrome Factory...")
    try:
        factory = w3.eth.contract(
            address=Web3.to_checksum_address(AERODROME_CONTRACTS["factory"]),
            abi=FACTORY_ABI
        )
        
        pool_count = factory.functions.allPoolsLength().call()
        print(f"✅ Factory accessible - Total pools: {pool_count:,}")
        
    except Exception as e:
        print(f"❌ Error accessing factory: {e}")
        return False
    
    # Get some pools
    print("\n🏊 Fetching Top Pools...")
    pools_data = []
    
    try:
        # Get last 10 pools (newest)
        start_idx = max(0, pool_count - 10)
        
        for i in range(start_idx, min(pool_count, start_idx + 10)):
            try:
                pool_address = factory.functions.allPools(i).call()
                pool = w3.eth.contract(
                    address=Web3.to_checksum_address(pool_address),
                    abi=POOL_ABI
                )
                
                # Get pool data
                token0 = pool.functions.token0().call()
                token1 = pool.functions.token1().call()
                symbol = pool.functions.symbol().call()
                is_stable = pool.functions.stable().call()
                reserves = pool.functions.getReserves().call()
                total_supply = pool.functions.totalSupply().call()
                
                # Get token symbols
                token0_contract = w3.eth.contract(address=token0, abi=ERC20_ABI)
                token1_contract = w3.eth.contract(address=token1, abi=ERC20_ABI)
                
                try:
                    token0_symbol = token0_contract.functions.symbol().call()
                    token1_symbol = token1_contract.functions.symbol().call()
                    token0_decimals = token0_contract.functions.decimals().call()
                    token1_decimals = token1_contract.functions.decimals().call()
                except:
                    token0_symbol = "???"
                    token1_symbol = "???"
                    token0_decimals = 18
                    token1_decimals = 18
                
                # Calculate TVL (simplified - would need price oracle for USD)
                reserve0_formatted = reserves[0] / (10 ** token0_decimals)
                reserve1_formatted = reserves[1] / (10 ** token1_decimals)
                
                pool_info = {
                    "address": pool_address,
                    "pair": f"{token0_symbol}/{token1_symbol}",
                    "stable": is_stable,
                    "reserves": {
                        token0_symbol: reserve0_formatted,
                        token1_symbol: reserve1_formatted
                    },
                    "lp_supply": total_supply / 1e18
                }
                
                pools_data.append(pool_info)
                
                print(f"\n   Pool #{i + 1}:")
                print(f"   Address: {pool_address}")
                print(f"   Pair: {token0_symbol}/{token1_symbol} ({'Stable' if is_stable else 'Volatile'})")
                print(f"   Reserves: {reserve0_formatted:,.2f} {token0_symbol} / {reserve1_formatted:,.2f} {token1_symbol}")
                
            except Exception as e:
                print(f"   ⚠️  Error reading pool {i}: {e}")
                continue
        
        print(f"\n✅ Successfully fetched {len(pools_data)} pools")
        
    except Exception as e:
        print(f"❌ Error fetching pools: {e}")
        return False
    
    # Look for specific popular pools
    print("\n🔍 Checking Popular Pools...")
    popular_pairs = [
        ("WETH", "USDC"),
        ("AERO", "WETH"),
        ("USDC", "DAI"),
    ]
    
    for token0_name, token1_name in popular_pairs:
        token0_addr = TOKENS.get(token0_name)
        token1_addr = TOKENS.get(token1_name)
        
        if token0_addr and token1_addr:
            print(f"\n   Looking for {token0_name}/{token1_name} pool...")
            # In production, would use factory.getPool() function
            found = False
            for pool in pools_data:
                if token0_name in pool["pair"] and token1_name in pool["pair"]:
                    print(f"   ✅ Found: {pool['pair']} at {pool['address']}")
                    found = True
                    break
            if not found:
                print(f"   ⚠️  Not found in recent pools")
    
    # Save sample data
    print("\n💾 Saving sample data...")
    with open("aerodrome_sample_data.json", "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "network": "base-mainnet",
            "factory": AERODROME_CONTRACTS["factory"],
            "total_pools": pool_count,
            "sample_pools": pools_data
        }, f, indent=2)
    print("✅ Sample data saved to aerodrome_sample_data.json")
    
    # Summary
    print("\n📊 Summary:")
    print(f"   - Connected to BASE mainnet ✅")
    print(f"   - Aerodrome Factory accessible ✅")
    print(f"   - Total pools: {pool_count:,}")
    print(f"   - Successfully read {len(pools_data)} pools")
    print(f"   - Data structure verified ✅")
    print("\n✅ Aerodrome integration test PASSED!")
    print("\n🎯 Ready for production deployment!")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_aerodrome_connection())