"""
Minimal CDP wrapper for Cloud Function
Extracted from project's CDP client to work standalone
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from web3 import Web3

logger = logging.getLogger(__name__)

# Aerodrome contract addresses on BASE mainnet
AERODROME_FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"

# ABI fragments
FACTORY_ABI = {
    "allPoolsLength": {
        "inputs": [],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    "allPools": {
        "inputs": [{"type": "uint256"}],
        "outputs": [{"type": "address"}],
        "stateMutability": "view", 
        "type": "function"
    }
}

POOL_ABI = {
    "getReserves": {
        "inputs": [],
        "outputs": [
            {"type": "uint256", "name": "_reserve0"},
            {"type": "uint256", "name": "_reserve1"},
            {"type": "uint256", "name": "_blockTimestampLast"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    "token0": {
        "inputs": [],
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    "token1": {
        "inputs": [],
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    "stable": {
        "inputs": [],
        "outputs": [{"type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    "totalSupply": {
        "inputs": [],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
}


class SimpleCDPClient:
    """Simplified CDP client using Web3 to interact with BASE mainnet"""
    
    def __init__(self):
        # Use Coinbase Cloud's public BASE RPC endpoint
        # This is the CDP-recommended endpoint for BASE mainnet
        self.rpc_url = "https://base-mainnet.g.alchemy.com/v2/demo"  # Public CDP endpoint
        self.w3 = None
        
    def initialize(self):
        """Initialize Web3 connection"""
        try:
            # Try multiple RPC endpoints
            rpc_endpoints = [
                "https://base-mainnet.g.alchemy.com/v2/demo",
                "https://mainnet.base.org",
                "https://base.publicnode.com",
                "https://base.llamarpc.com"
            ]
            
            for rpc_url in rpc_endpoints:
                try:
                    logger.info(f"Trying RPC endpoint: {rpc_url}")
                    self.w3 = Web3(Web3.HTTPProvider(
                        rpc_url,
                        request_kwargs={'timeout': 10}
                    ))
                    
                    if self.w3.is_connected():
                        logger.info(f"Connected to BASE via {rpc_url}, block: {self.w3.eth.block_number}")
                        return True
                except Exception as e:
                    logger.warning(f"Failed with {rpc_url}: {e}")
                    continue
                    
            logger.error("Failed to connect to any RPC endpoint")
            return False
                
        except Exception as e:
            logger.error(f"Failed to initialize connection: {e}")
            return False
    
    async def read_contract(self, contract_address: str, method: str, abi: Dict[str, Any], args: list = None):
        """Read data from contract"""
        try:
            if not self.w3:
                return None
                
            # Create contract instance
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=[abi]
            )
            
            # Call the method
            if args:
                result = contract.functions[method](*args).call()
            else:
                result = contract.functions[method]().call()
                
            return result
            
        except Exception as e:
            logger.error(f"Error reading {method} from {contract_address}: {e}")
            return None


class AerodromeCDP:
    """Aerodrome integration using CDP"""
    
    def __init__(self, cdp_client):
        self.cdp = cdp_client
        self.factory_address = AERODROME_FACTORY
        
    async def get_pool_count(self) -> Optional[int]:
        """Get total number of pools from factory"""
        try:
            result = await self.cdp.read_contract(
                contract_address=self.factory_address,
                method="allPoolsLength",
                abi=FACTORY_ABI["allPoolsLength"]
            )
            return int(result) if result is not None else None
            
        except Exception as e:
            logger.error(f"Failed to get pool count: {e}")
            return None
    
    async def get_pool_address(self, index: int) -> Optional[str]:
        """Get pool address by index"""
        try:
            result = await self.cdp.read_contract(
                contract_address=self.factory_address,
                method="allPools",
                args=[index],
                abi=FACTORY_ABI["allPools"]
            )
            return result
            
        except Exception as e:
            logger.error(f"Failed to get pool address: {e}")
            return None
    
    async def get_pool_data(self, pool_address: str) -> Optional[Dict[str, Any]]:
        """Fetch pool data from contract"""
        try:
            # Get all pool data in parallel
            token0 = await self.cdp.read_contract(
                contract_address=pool_address,
                method="token0",
                abi=POOL_ABI["token0"]
            )
            
            token1 = await self.cdp.read_contract(
                contract_address=pool_address,
                method="token1",
                abi=POOL_ABI["token1"]
            )
            
            reserves = await self.cdp.read_contract(
                contract_address=pool_address,
                method="getReserves",
                abi=POOL_ABI["getReserves"]
            )
            
            is_stable = await self.cdp.read_contract(
                contract_address=pool_address,
                method="stable",
                abi=POOL_ABI["stable"]
            )
            
            total_supply = await self.cdp.read_contract(
                contract_address=pool_address,
                method="totalSupply",
                abi=POOL_ABI["totalSupply"]
            )
            
            return {
                "address": pool_address,
                "token0": token0,
                "token1": token1,
                "reserve0": reserves[0] if reserves else 0,
                "reserve1": reserves[1] if reserves else 0,
                "is_stable": is_stable if is_stable is not None else False,
                "total_supply": total_supply if total_supply is not None else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get pool data: {e}")
            return None