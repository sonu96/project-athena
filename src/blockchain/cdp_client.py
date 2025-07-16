"""
CDP AgentKit Integration

Handles all blockchain interactions through Coinbase Developer Platform.
"""

import logging
from typing import Dict, Any, Optional
import json
import os

from ..config import settings

logger = logging.getLogger(__name__)

# Try to import CDP SDK
try:
    from cdp import CdpClient
    CDP_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import
        from coinbase.wallet.client import Client
        from coinbase.wallet.model import Account
        CDP_AVAILABLE = False  # Different API, still use simulation
        logger.warning("Using Coinbase Client instead of CDP SDK. Running in simulation mode.")
    except ImportError:
        logger.warning("CDP SDK not available. Running in simulation mode.")
        CDP_AVAILABLE = False


class CDPClient:
    """
    Client for interacting with CDP AgentKit
    
    Handles:
    - Wallet management
    - Balance queries
    - Gas price monitoring
    - Transaction execution (V2)
    """
    
    def __init__(self):
        self.wallet = None
        self.network = settings.network
        self.cdp_client = None
        
        # Try to initialize CDP first
        if CDP_AVAILABLE and not settings.observation_mode:
            self._initialize_cdp()
        
        # Set simulation mode based on whether CDP initialized successfully
        if not self.cdp_client:
            self.simulation_mode = True
            logger.info("🎮 CDP running in simulation mode")
        else:
            self.simulation_mode = False
        
        # Always initialize simulation balance
        self._simulation_balance = settings.starting_treasury
    
    def _initialize_cdp(self):
        """Initialize CDP SDK"""
        try:
            # CDP SDK expects these exact environment variable names
            os.environ["CDP_API_KEY_ID"] = settings.cdp_api_key_name
            os.environ["CDP_API_KEY_SECRET"] = settings.cdp_api_key_secret
            
            # Create CDP client
            self.cdp_client = CdpClient()
            self.simulation_mode = False
            
            logger.info(f"✅ CDP configured for {self.network}")
            
        except Exception as e:
            logger.error(f"Failed to initialize CDP: {e}")
            self.simulation_mode = True
    
    async def initialize_wallet(self) -> Dict[str, Any]:
        """
        Initialize or load wallet
        
        Returns:
            Wallet info including address
        """
        if self.simulation_mode:
            return {
                "address": "0xSIMULATED1234567890",
                "network": self.network,
                "mode": "simulation"
            }
        
        try:
            # Check if we have an existing wallet address in environment
            existing_address = os.getenv("CDP_WALLET_ADDRESS")
            
            if existing_address:
                # Use existing wallet address
                logger.info(f"✅ Using existing wallet: {existing_address}")
                self.wallet_address = existing_address
                
                # Try to load wallet from CDP
                try:
                    wallets = await self.cdp_client.list_wallets()
                    for wallet in wallets:
                        if wallet.default_address == existing_address:
                            self.wallet = wallet
                            break
                except:
                    pass
                    
                return {
                    "address": existing_address,
                    "network": self.network,
                    "mode": "live"
                }
            else:
                # Create new wallet on BASE
                self.wallet = await self.cdp_client.create_wallet(network_id="base-mainnet")
                
                logger.info(f"✅ Created new wallet: {self.wallet.default_address}")
                
                return {
                    "address": self.wallet.default_address,
                    "network": self.wallet.network_id,
                    "mode": "live"
                }
            
        except Exception as e:
            logger.error(f"Failed to initialize wallet: {e}")
            self.simulation_mode = True
            return {
                "address": "0xERROR",
                "network": self.network,
                "mode": "error",
                "error": str(e)
            }
    
    async def get_wallet_balance(self) -> float:
        """
        Get wallet balance in USD
        
        Returns:
            Balance in USD
        """
        if self.simulation_mode:
            return self._simulation_balance
        
        try:
            if not self.wallet:
                await self.initialize_wallet()
            
            # Get ETH balance
            eth_balance = float(self.wallet.balance("eth"))
            
            # Get USDC balance (if any)
            usdc_balance = 0.0
            try:
                usdc_balance = float(self.wallet.balance("usdc"))
            except:
                pass
            
            # Estimate USD value (rough calculation)
            eth_price = 2500  # Approximate, should fetch real price
            total_usd = (eth_balance * eth_price) + usdc_balance
            
            logger.debug(f"Balance: {eth_balance:.4f} ETH + {usdc_balance:.2f} USDC ≈ ${total_usd:.2f}")
            
            return total_usd
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return self._simulation_balance
    
    async def get_gas_price(self) -> float:
        """
        Get current gas price in gwei
        
        Returns:
            Gas price in gwei
        """
        if self.simulation_mode:
            # Simulate varying gas prices
            import random
            base_gas = 15
            variation = random.uniform(-5, 10)
            return max(5, base_gas + variation)
        
        try:
            # Get gas price from network
            # This is a simplified version - real implementation would use web3
            gas_price_wei = 15_000_000_000  # 15 gwei default
            gas_price_gwei = gas_price_wei / 1e9
            
            return gas_price_gwei
            
        except Exception as e:
            logger.error(f"Failed to get gas price: {e}")
            return 20.0  # Default fallback
    
    async def estimate_transaction_cost(self, gas_limit: int = 21000) -> float:
        """
        Estimate transaction cost in USD
        
        Args:
            gas_limit: Estimated gas usage
            
        Returns:
            Estimated cost in USD
        """
        gas_price = await self.get_gas_price()
        
        # Calculate cost in ETH
        cost_eth = (gas_price * gas_limit) / 1e9
        
        # Convert to USD (rough estimate)
        eth_price = 2500
        cost_usd = cost_eth * eth_price
        
        return cost_usd
    
    def get_wallet_address(self) -> str:
        """Get wallet address"""
        if self.simulation_mode:
            return "0xSIMULATED1234567890"
        
        if self.wallet:
            return self.wallet.default_address.address
        
        return "0xNOT_INITIALIZED"
    
    async def sign_message(self, message: str) -> str:
        """
        Sign a message with the wallet (for authentication)
        
        Args:
            message: Message to sign
            
        Returns:
            Signature
        """
        if self.simulation_mode:
            return "SIMULATED_SIGNATURE"
        
        try:
            if not self.wallet:
                await self.initialize_wallet()
            
            # CDP SDK should have a sign method
            # This is placeholder - check actual CDP API
            signature = "0x" + "00" * 65  # Placeholder
            
            return signature
            
        except Exception as e:
            logger.error(f"Failed to sign message: {e}")
            return "ERROR_SIGNATURE"
    
    async def invoke_contract(self, contract_address: str, method: str, abi: Dict[str, Any], args: list = None) -> Any:
        """
        Invoke a smart contract method using CDP
        
        Args:
            contract_address: Contract address
            method: Method name to call
            abi: Method ABI
            args: Method arguments
            
        Returns:
            Contract response
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Would invoke {method} on {contract_address}")
            return None
        
        try:
            if not self.wallet:
                await self.initialize_wallet()
            
            # CDP SDK contract invocation
            result = self.wallet.invoke_contract(
                contract_address=contract_address,
                method=method,
                abi=json.dumps(abi),
                args=args or []
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to invoke contract: {e}")
            return None
    
    async def read_contract(self, contract_address: str, method: str, abi: Dict[str, Any], args: list = None) -> Any:
        """
        Read data from a smart contract using CDP
        
        Args:
            contract_address: Contract address
            method: Method name to call
            abi: Method ABI
            args: Method arguments
            
        Returns:
            Contract response
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Would read {method} from {contract_address}")
            return None
        
        try:
            if not self.wallet:
                await self.initialize_wallet()
            
            # Import necessary CDP classes
            from cdp import ContractCall, EncodedCall
            
            # Create contract call
            if isinstance(abi, dict):
                # Single function ABI
                contract_abi = [abi]
            else:
                contract_abi = abi
                
            # Use EncodedCall for contract reading
            call = EncodedCall(
                to=contract_address,
                data=self._encode_function_data(method, contract_abi, args or [])
            )
            
            # Execute the call
            result = await self.wallet.invoke_contract(
                contract_call=call
            )
            
            return self._decode_result(result, abi)
            
        except Exception as e:
            logger.error(f"Failed to read contract: {e}")
            return None
    
    def _encode_function_data(self, method: str, abi: list, args: list) -> str:
        """Encode function call data"""
        try:
            from web3 import Web3
            
            # Create function signature
            function_abi = None
            for item in abi:
                if item.get("name") == method:
                    function_abi = item
                    break
                    
            if not function_abi:
                return "0x"
                
            # Encode the function call
            w3 = Web3()
            contract = w3.eth.contract(abi=abi)
            return contract.encodeABI(fn_name=method, args=args)
            
        except Exception as e:
            logger.error(f"Failed to encode function data: {e}")
            return "0x"
    
    def _decode_result(self, result: Any, abi: Dict[str, Any]) -> Any:
        """Decode contract call result"""
        try:
            if not result:
                return None
                
            # Simple decoding for common types
            outputs = abi.get("outputs", [])
            if outputs and outputs[0]["type"] == "uint256":
                return int(result, 16) if isinstance(result, str) else result
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to decode result: {e}")
            return result