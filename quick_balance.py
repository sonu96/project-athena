#!/usr/bin/env python3
"""Quick balance check"""
import json
from web3 import Web3

# Load wallet
with open("wallet_data/athena_production_wallet.json") as f:
    wallet = json.load(f)

address = wallet["address"]
print(f"🏠 Wallet: {address}")

# Connect to Base Sepolia
w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
balance = w3.eth.get_balance(address)
eth = w3.from_wei(balance, "ether")

print(f"💰 Balance: {eth} ETH")
print(f"🔍 Explorer: https://sepolia.basescan.org/address/{address}")