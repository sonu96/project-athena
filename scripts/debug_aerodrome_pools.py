#!/usr/bin/env python3
"""Debug Aerodrome pool fetching"""

from web3 import Web3
import json

# Connect to BASE
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
print(f"Connected: {w3.is_connected()}")
print(f"Chain ID: {w3.eth.chain_id}")

# Factory address
FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"

# Factory ABI
FACTORY_ABI = json.loads('[{"inputs":[],"name":"allPoolsLength","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"type":"uint256"}],"name":"allPools","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"}]')

# Pool ABI
POOL_ABI = json.loads('[{"inputs":[],"name":"token0","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token1","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getReserves","outputs":[{"type":"uint256","name":"_reserve0"},{"type":"uint256","name":"_reserve1"},{"type":"uint256","name":"_blockTimestampLast"}],"stateMutability":"view","type":"function"}]')

factory = w3.eth.contract(address=Web3.to_checksum_address(FACTORY), abi=FACTORY_ABI)

# Get pool count
pool_count = factory.functions.allPoolsLength().call()
print(f"\nTotal pools: {pool_count}")

# Check last 5 pools
print("\nChecking last 5 pools:")
for i in range(max(0, pool_count - 5), pool_count):
    try:
        pool_addr = factory.functions.allPools(i).call()
        print(f"\nPool {i}: {pool_addr}")
        
        pool = w3.eth.contract(address=pool_addr, abi=POOL_ABI)
        token0 = pool.functions.token0().call()
        token1 = pool.functions.token1().call()
        reserves = pool.functions.getReserves().call()
        
        print(f"  Token0: {token0}")
        print(f"  Token1: {token1}")
        print(f"  Reserve0: {reserves[0]}")
        print(f"  Reserve1: {reserves[1]}")
        
    except Exception as e:
        print(f"  Error: {e}")