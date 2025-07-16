#!/usr/bin/env python3.11
"""Validate CDP SDK connection and Aerodrome data access"""

import os
import asyncio
from dotenv import load_dotenv

# Load mainnet configuration
load_dotenv('.env.mainnet')

# Add src to path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.blockchain.cdp_client import CDPClient
from src.aerodrome.observer import AerodromeObserver

async def validate_cdp_aerodrome():
    """Validate CDP and Aerodrome integration"""
    print("\n🚀 Validating CDP SDK with Aerodrome on BASE Mainnet\n")
    
    # Initialize CDP client
    print("1. Initializing CDP Client...")
    cdp_client = CDPClient()
    
    if cdp_client.simulation_mode:
        print("   ⚠️  CDP is in simulation mode")
        print("   Please ensure:")
        print("   - Python 3.10+ is being used")
        print("   - CDP SDK is installed: pip install cdp-sdk")
        print("   - API keys are correctly set in .env.mainnet")
    else:
        print("   ✅ CDP Client initialized")
    
    # Initialize wallet
    print("\n2. Setting up wallet...")
    wallet_info = await cdp_client.initialize_wallet()
    print(f"   Address: {wallet_info['address']}")
    print(f"   Network: {wallet_info['network']}")
    print(f"   Mode: {wallet_info['mode']}")
    
    # Check balance
    print("\n3. Checking wallet balance...")
    balance = await cdp_client.get_wallet_balance()
    print(f"   Balance: ${balance:.2f} USD")
    
    # Initialize Aerodrome observer
    print("\n4. Initializing Aerodrome Observer...")
    observer = AerodromeObserver(cdp_client)
    print(f"   Mode: {'Simulation' if observer.simulation_mode else 'Live CDP'}")
    
    # Get top pools
    print("\n5. Fetching Aerodrome pools...")
    pools = await observer.get_top_pools(limit=3)
    
    if pools:
        print(f"   ✅ Found {len(pools)} pools:")
        for pool in pools:
            symbol = pool.get('symbol', f"{pool.get('token0_symbol', '???')}/{pool.get('token1_symbol', '???')}")
            print(f"\n   Pool: {symbol}")
            print(f"   Address: {pool['address']}")
            print(f"   TVL: ${pool['tvl_usd']:,.2f}")
            print(f"   Type: {pool['type']}")
    else:
        print("   ⚠️  No pools found")
    
    # Test contract read directly
    if not cdp_client.simulation_mode:
        print("\n6. Testing direct contract read...")
        factory_address = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
        
        pool_count = await cdp_client.read_contract(
            contract_address=factory_address,
            method="allPoolsLength",
            abi={
                "inputs": [],
                "name": "allPoolsLength",
                "outputs": [{"type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        )
        
        if pool_count:
            print(f"   ✅ Aerodrome has {pool_count} total pools")
        else:
            print("   ⚠️  Could not read pool count")
    
    print("\n✅ Validation complete!")
    
    if cdp_client.simulation_mode:
        print("\n⚠️  Running in simulation mode. To use real data:")
        print("   1. Ensure Python 3.10+ is used")
        print("   2. Add your wallet address to CDP_WALLET_ADDRESS in .env.mainnet")
        print("   3. Run with: python3.11 validate_cdp.py")

if __name__ == "__main__":
    asyncio.run(validate_cdp_aerodrome())