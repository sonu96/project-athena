#!/usr/bin/env python3.11
"""Test CDP SDK with real Aerodrome data"""

import os
import asyncio
from cdp import CdpClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_cdp_aerodrome():
    """Test real CDP SDK functionality"""
    print("\n🚀 Testing CDP SDK with BASE Mainnet\n")
    
    # Create CDP client
    print("1. Creating CDP Client...")
    try:
        # Set environment variables for CDP
        os.environ["CDP_API_KEY_ID"] = os.getenv("CDP_API_KEY_NAME", "")
        os.environ["CDP_API_KEY_SECRET"] = os.getenv("CDP_API_KEY_SECRET", "")
        
        cdp = CdpClient()
        print("   ✅ CDP client created")
    except Exception as e:
        print(f"   ❌ Failed to create CDP client: {e}")
        return
    
    # Create/load wallet
    print("\n2. Setting up wallet...")
    try:
        # Create wallet on BASE network
        wallet = await cdp.create_wallet(network_id="base-mainnet")
        print(f"   ✅ Wallet address: {wallet.default_address}")
        print(f"   🌐 Network: {wallet.network_id}")
        
    except Exception as e:
        print(f"   ❌ Wallet error: {e}")
        return
    
    # Test contract reading - Aerodrome Factory
    print("\n3. Testing Aerodrome Factory contract read...")
    factory_address = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
    
    try:
        # Read allPoolsLength from factory
        from cdp import ContractCall
        
        # Create contract call
        call = ContractCall(
            address=factory_address,
            method="allPoolsLength",
            abi={
                "inputs": [],
                "name": "allPoolsLength",
                "outputs": [{"type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        )
        
        # Execute call
        result = await wallet.read_contract(call)
        print(f"   ✅ Total pools in Aerodrome: {result}")
        
    except Exception as e:
        print(f"   ❌ Contract read error: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Try alternative method
        try:
            print("\n   Trying alternative approach...")
            # Check available methods on wallet
            print(f"   Wallet methods: {[m for m in dir(wallet) if not m.startswith('_')][:10]}")
        except Exception as e2:
            print(f"   Alternative error: {e2}")
    
    print("\n✅ CDP SDK test complete!")

if __name__ == "__main__":
    asyncio.run(test_cdp_aerodrome())