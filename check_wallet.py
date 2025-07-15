#!/usr/bin/env python3
"""
Quick script to check a wallet address on Base Sepolia
"""

import asyncio
import aiohttp

async def check_wallet(address: str):
    """Check wallet on Base Sepolia explorer"""
    print(f"🔍 Checking wallet: {address}")
    print(f"📊 Base Sepolia Explorer: https://sepolia.basescan.org/address/{address}")
    
    # You can also check via Etherscan API if you have a key
    # For now, just display the link
    print("\nTo view:")
    print("1. Click the link above")
    print("2. Check ETH balance and transaction history")
    print("3. The agent will use this wallet if it matches your CDP wallet")
    
    # Check if this matches CDP wallet format
    if address.startswith("0x") and len(address) == 42:
        print("\n✅ Valid Ethereum address format")
    else:
        print("\n❌ Invalid address format")

if __name__ == "__main__":
    wallet_address = "0x9E104899c35B4A2abD94f5C15F099789120e6a1B"
    asyncio.run(check_wallet(wallet_address))