#!/usr/bin/env python3
"""
Test script to verify CDP integration is working correctly
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.integrations.cdp_integration import CDPIntegration
from src.config.settings import settings


async def test_cdp():
    """Test CDP integration"""
    print("🧪 Testing CDP Integration...")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Checking environment variables...")
    has_key_name = bool(os.getenv("CDP_API_KEY_NAME"))
    has_key_secret = bool(os.getenv("CDP_API_KEY_SECRET"))
    
    print(f"CDP_API_KEY_NAME: {'✅ Set' if has_key_name else '❌ Not set'}")
    print(f"CDP_API_KEY_SECRET: {'✅ Set' if has_key_secret else '❌ Not set'}")
    print(f"NETWORK: {settings.network}")
    
    if not (has_key_name and has_key_secret):
        print("\n❌ Missing CDP credentials!")
        print("Please follow the CDP setup guide in docs/cdp_setup_guide.md")
        return
    
    # Test CDP integration
    cdp = CDPIntegration()
    
    # Initialize wallet
    print("\n🔑 Initializing wallet...")
    try:
        success = await cdp.initialize_wallet()
        if not success:
            print("❌ Failed to initialize wallet")
            print("Check your CDP credentials and network connection")
            return
        print("✅ Wallet initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing wallet: {e}")
        return
    
    # Get wallet info
    print("\n💰 Getting wallet balance...")
    try:
        balance = await cdp.get_wallet_balance()
        print(f"Wallet address: {cdp.wallet.default_address if cdp.wallet else 'N/A'}")
        print(f"Network: {cdp.network}")
        print(f"Balance: {balance}")
        
        if balance.get("simulation"):
            print("\n⚠️  Running in simulation mode (CDP SDK not available)")
            print("To use real CDP, ensure you're using Python 3.10+ and have cdp-sdk installed")
    except Exception as e:
        print(f"❌ Error getting balance: {e}")
    
    # Test network status
    print("\n🌐 Testing network status...")
    try:
        status = await cdp.get_network_status()
        print(f"Network connected: {status.get('connected')}")
        print(f"Network: {status.get('network')}")
        if status.get('wallet_address'):
            print(f"Wallet: {status.get('wallet_address')}")
    except Exception as e:
        print(f"❌ Error getting network status: {e}")
    
    # Request testnet tokens (optional)
    print("\n🚰 Would you like to request testnet tokens? (y/n): ", end="")
    try:
        # Non-blocking input with timeout
        import select
        import termios
        import tty
        
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            ready = select.select([sys.stdin], [], [], 5.0)  # 5 second timeout
            if ready[0]:
                answer = sys.stdin.read(1).lower()
            else:
                answer = 'n'
                print("n (timeout)")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        if answer == 'y':
            print("\nRequesting testnet tokens...")
            faucet_success = await cdp.get_testnet_tokens()
            if faucet_success:
                print("✅ Testnet tokens requested successfully")
                print("Note: It may take a few minutes for tokens to appear")
            else:
                print("❌ Failed to request testnet tokens")
    except:
        # Fallback for systems without termios
        print("n (skipped)")
    
    print("\n✅ CDP test complete!")
    print("\nNext steps:")
    print("1. If wallet was created, check wallet_data/athena_wallet.json")
    print("2. View your wallet on Base Sepolia explorer:")
    if cdp.wallet and hasattr(cdp.wallet, 'default_address'):
        print(f"   https://sepolia.basescan.org/address/{cdp.wallet.default_address}")
    print("3. Run the agent with: python -m src.core.agent")


if __name__ == "__main__":
    print("🏛️ Athena DeFi Agent - CDP Test")
    print("================================\n")
    
    # Check Python version
    import sys
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 10):
        print("⚠️  Warning: Python 3.10+ recommended for CDP SDK")
    
    # Run test
    asyncio.run(test_cdp())