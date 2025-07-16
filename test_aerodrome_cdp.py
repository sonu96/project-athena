#!/usr/bin/env python3
"""Test Aerodrome data fetching using CDP AgentKit"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.blockchain.cdp_client import CDPClient

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

async def test_cdp_aerodrome():
    """Test Aerodrome data access via CDP AgentKit"""
    print("\n🚀 Testing Aerodrome Data Access via CDP AgentKit\n")
    
    try:
        # Initialize CDP client
        print("1. Initializing CDP Client...")
        cdp_client = CDPClient()
        print("   ✅ CDP Client initialized")
        
        # Get wallet info
        print("\n2. CDP Wallet Info:")
        wallet_address = cdp_client.get_wallet_address()
        print(f"   Address: {wallet_address}")
        print(f"   Network: {cdp_client.network}")
        
        # Check if we're on BASE
        if cdp_client.network != 'base':
            print(f"   ⚠️  Warning: Not on BASE mainnet (current: {cdp_client.network})")
        
        # Get balance
        print("\n3. Wallet Balance:")
        balance = await cdp_client.get_wallet_balance()
        print(f"   Balance (USD): ${balance:.2f}")
        
        # Test contract reads via CDP
        print("\n4. Testing Aerodrome Contract Reads via CDP...")
        
        # Factory ABI for getting pool count
        factory_abi = [{
            "inputs": [],
            "name": "allPoolsLength",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        # Read pool count
        print("   Reading total pool count from factory...")
        try:
            # CDP AgentKit should handle contract reads
            # This is how we would read from contracts using CDP
            result = cdp_client.read_contract(
                contract_address=AERODROME_CONTRACTS["factory"],
                method="allPoolsLength",
                abi=factory_abi
            )
            print(f"   ✅ Total pools: {result}")
        except AttributeError:
            print("   ⚠️  CDP read_contract method not implemented")
            print("   Note: CDP AgentKit may require specific methods for contract interaction")
        except Exception as e:
            print(f"   ❌ Error reading contract: {e}")
        
        # Test token balance reads
        print("\n5. Testing Token Balance Reads...")
        for token_name, token_address in TOKENS.items():
            try:
                # CDP might have a specific method for token balances
                balance = cdp_client.get_token_balance(token_address)
                print(f"   {token_name}: {balance}")
            except AttributeError:
                print(f"   ⚠️  Token balance method not available for {token_name}")
                break
            except Exception as e:
                print(f"   ❌ Error reading {token_name}: {e}")
        
        # Check available CDP methods
        print("\n6. Available CDP Methods:")
        methods = [method for method in dir(cdp_client) if not method.startswith('_')]
        for method in methods[:10]:  # Show first 10 methods
            print(f"   - {method}")
        
        # Summary
        print("\n📊 CDP AgentKit Status:")
        print("   ✅ CDP Client connected")
        print("   ✅ Wallet accessible")
        print("   ⚠️  Contract reading needs CDP-specific implementation")
        print("\n💡 Next Steps:")
        print("   1. Implement Aerodrome observer using CDP-compatible methods")
        print("   2. Use CDP's built-in DeFi integrations if available")
        print("   3. Consider using CDP's transaction simulation for pool analysis")
        
    except Exception as e:
        print(f"\n❌ Error during CDP test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cdp_aerodrome())