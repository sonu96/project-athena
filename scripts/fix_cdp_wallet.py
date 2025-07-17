#!/usr/bin/env python3
"""Fix CDP wallet initialization and test connection"""

import os
import json
import asyncio
from cdp import Wallet, Cdp
from dotenv import load_dotenv

load_dotenv()

async def fix_cdp_wallet():
    """Initialize CDP wallet properly and save credentials"""
    
    print("🔧 Fixing CDP Wallet Initialization\n")
    
    # Initialize CDP
    try:
        # Use API keys from environment
        api_key_name = os.getenv("CDP_API_KEY_NAME")
        api_key_secret = os.getenv("CDP_API_KEY_SECRET")
        
        if not api_key_name or not api_key_secret:
            print("❌ CDP API keys not found in environment")
            return False
            
        print(f"✅ Found CDP API keys")
        
        # Configure CDP
        Cdp.configure(api_key_name, api_key_secret)
        print("✅ CDP configured successfully")
        
        # Create a new wallet for mainnet
        print("\n📱 Creating new wallet for BASE mainnet...")
        wallet = Wallet.create(network_id="base-mainnet")
        
        # Get wallet details
        address = wallet.default_address.address_id
        print(f"✅ Wallet created: {address}")
        
        # Export wallet data for persistence
        wallet_data = wallet.export()
        
        # Save wallet credentials securely
        wallet_info = {
            "address": address,
            "network": "base-mainnet",
            "wallet_id": wallet.id,
            "seed": wallet_data.seed,
            "created_at": str(wallet_data.created_at)
        }
        
        # Save to secure location
        with open(".cdp_wallet.json", "w") as f:
            json.dump(wallet_info, f, indent=2)
        
        print("\n💾 Wallet info saved to .cdp_wallet.json")
        
        # Test wallet by checking balance
        print("\n🔍 Testing wallet...")
        balances = wallet.balances()
        print(f"✅ Wallet balance check successful")
        for asset, amount in balances.items():
            print(f"   {asset}: {amount}")
        
        # Update CDP status
        cdp_status = {
            "cdp_working": True,
            "wallet_address": address,
            "network": "base-mainnet",
            "initialized": True,
            "note": "Wallet successfully created and initialized"
        }
        
        with open("cdp_status.json", "w") as f:
            json.dump(cdp_status, f, indent=2)
        
        print("\n✅ CDP wallet fixed and ready for mainnet operations!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        # Try to provide helpful error messages
        if "API key" in str(e):
            print("\n💡 Make sure your .env file contains:")
            print("   CDP_API_KEY_NAME=your-key-name")
            print("   CDP_API_KEY_SECRET=your-key-secret")
        elif "network" in str(e):
            print("\n💡 Network issue - trying with base network ID...")
            # Try alternative network ID
            try:
                Cdp.configure(api_key_name, api_key_secret)
                wallet = Wallet.create(network_id="8453")  # BASE chain ID
                print("✅ Wallet created with chain ID")
                return True
            except:
                pass
        
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_cdp_wallet())
    if not success:
        print("\n🔧 Please check your CDP credentials and try again")