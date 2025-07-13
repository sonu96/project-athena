from typing import Dict, Any, List
from mcp import Tool, ToolCall
from .models import DecisionContext, DecisionResult
from .treasury import TreasuryManager
from .memory import MemoryManager
import httpx
import asyncio
from web3 import Web3
from eth_account import Account
import json

class BaseBlockchainTool(Tool):
    """MCP Tool for Base blockchain operations"""
    
    def __init__(self, rpc_url: str = "https://mainnet.base.org", private_key: str = None):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key) if private_key else None
        self.chain_id = 8453  # Base mainnet
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "base_blockchain",
            "description": "Interact with Base blockchain for DeFi operations",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "get_balance", "get_gas_price", "get_block_number",
                            "send_transaction", "get_transaction", "get_contract_balance",
                            "approve_token", "swap_tokens", "stake_tokens", "unstake_tokens"
                        ]
                    },
                    "address": {"type": "string"},
                    "amount": {"type": "string"},
                    "token_address": {"type": "string"},
                    "spender_address": {"type": "string"},
                    "protocol": {"type": "string"},
                    "gas_limit": {"type": "number"},
                    "gas_price": {"type": "string"}
                },
                "required": ["operation"]
            }
        }
    
    async def execute(self, call: ToolCall) -> Dict[str, Any]:
        operation = call.arguments["operation"]
        
        try:
            if operation == "get_balance":
                address = call.arguments["address"]
                balance = self.w3.eth.get_balance(address)
                return {
                    "balance": str(balance),
                    "balance_eth": self.w3.from_wei(balance, 'ether')
                }
            
            elif operation == "get_gas_price":
                gas_price = self.w3.eth.gas_price
                return {
                    "gas_price": str(gas_price),
                    "gas_price_gwei": self.w3.from_wei(gas_price, 'gwei')
                }
            
            elif operation == "get_block_number":
                block_number = self.w3.eth.block_number
                return {"block_number": block_number}
            
            elif operation == "send_transaction":
                if not self.account:
                    return {"error": "No private key configured"}
                
                to_address = call.arguments["address"]
                amount = call.arguments["amount"]
                gas_price = call.arguments.get("gas_price", self.w3.eth.gas_price)
                gas_limit = call.arguments.get("gas_limit", 21000)
                
                transaction = {
                    'to': to_address,
                    'value': self.w3.to_wei(amount, 'ether'),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.account.address),
                    'chainId': self.chain_id
                }
                
                signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                return {
                    "transaction_hash": tx_hash.hex(),
                    "from": self.account.address,
                    "to": to_address,
                    "amount": amount
                }
            
            elif operation == "get_transaction":
                tx_hash = call.arguments["address"]  # Using address field for tx_hash
                tx = self.w3.eth.get_transaction(tx_hash)
                return {
                    "transaction": {
                        "hash": tx_hash,
                        "from": tx['from'],
                        "to": tx['to'],
                        "value": str(tx['value']),
                        "gas": tx['gas'],
                        "gasPrice": str(tx['gasPrice']),
                        "nonce": tx['nonce']
                    }
                }
            
            elif operation == "get_contract_balance":
                contract_address = call.arguments["token_address"]
                user_address = call.arguments["address"]
                
                # ERC20 balanceOf function signature
                balance_of_signature = self.w3.keccak(text="balanceOf(address)")[:4]
                encoded_address = self.w3.to_bytes(hexstr=user_address[2:]).rjust(32, b'\x00')
                
                data = balance_of_signature + encoded_address
                result = self.w3.eth.call({
                    'to': contract_address,
                    'data': data
                })
                
                balance = int.from_bytes(result, 'big')
                return {"balance": str(balance)}
            
            elif operation == "approve_token":
                if not self.account:
                    return {"error": "No private key configured"}
                
                token_address = call.arguments["token_address"]
                spender_address = call.arguments["spender_address"]
                amount = call.arguments["amount"]
                
                # ERC20 approve function
                approve_signature = self.w3.keccak(text="approve(address,uint256)")[:4]
                encoded_spender = self.w3.to_bytes(hexstr=spender_address[2:]).rjust(32, b'\x00')
                encoded_amount = amount.to_bytes(32, 'big')
                
                data = approve_signature + encoded_spender + encoded_amount
                
                transaction = {
                    'to': token_address,
                    'data': data,
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.account.address),
                    'chainId': self.chain_id
                }
                
                signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                return {
                    "transaction_hash": tx_hash.hex(),
                    "token_address": token_address,
                    "spender": spender_address,
                    "amount": str(amount)
                }
            
            elif operation in ["swap_tokens", "stake_tokens", "unstake_tokens"]:
                protocol = call.arguments.get("protocol", "uniswap")
                amount = call.arguments["amount"]
                token_address = call.arguments["token_address"]
                
                # Simulate DeFi protocol interaction
                return {
                    "operation": operation,
                    "protocol": protocol,
                    "amount": amount,
                    "token_address": token_address,
                    "status": "simulated",
                    "transaction_hash": "0x" + "0" * 64,
                    "gas_used": 150000,
                    "gas_price": str(self.w3.eth.gas_price)
                }
            
            return {"error": "Unknown operation"}
            
        except Exception as e:
            return {"error": str(e)}

class Mem0Tool(Tool):
    """MCP Tool for Mem0 memory operations"""
    
    def __init__(self, mem0_client):
        self.mem0 = mem0_client
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "mem0",
            "description": "Persistent memory operations using Mem0",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "store_memory", "retrieve_memory", "search_memories",
                            "update_memory", "delete_memory", "get_memory_stats"
                        ]
                    },
                    "key": {"type": "string"},
                    "value": {"type": "object"},
                    "query": {"type": "string"},
                    "memory_type": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["operation"]
            }
        }
    
    async def execute(self, call: ToolCall) -> Dict[str, Any]:
        operation = call.arguments["operation"]
        
        try:
            if operation == "store_memory":
                key = call.arguments["key"]
                value = call.arguments["value"]
                metadata = call.arguments.get("metadata", {})
                
                # Store in Mem0
                await self.mem0.store(key, value, metadata)
                return {"status": "stored", "key": key}
            
            elif operation == "retrieve_memory":
                key = call.arguments["key"]
                memory = await self.mem0.retrieve(key)
                return {"memory": memory}
            
            elif operation == "search_memories":
                query = call.arguments["query"]
                memory_type = call.arguments.get("memory_type", "all")
                
                # Search in Mem0
                results = await self.mem0.search(query, memory_type)
                return {"results": results}
            
            elif operation == "update_memory":
                key = call.arguments["key"]
                value = call.arguments["value"]
                metadata = call.arguments.get("metadata", {})
                
                # Update in Mem0
                await self.mem0.update(key, value, metadata)
                return {"status": "updated", "key": key}
            
            elif operation == "delete_memory":
                key = call.arguments["key"]
                
                # Delete from Mem0
                await self.mem0.delete(key)
                return {"status": "deleted", "key": key}
            
            elif operation == "get_memory_stats":
                stats = await self.mem0.get_stats()
                return {"stats": stats}
            
            return {"error": "Unknown operation"}
            
        except Exception as e:
            return {"error": str(e)}

class MemoryTool(Tool):
    """MCP Tool for memory operations"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "memory",
            "description": "Query and record memories for the DeFi agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["query_survival", "record_survival", "query_strategy", "record_strategy"]
                    },
                    "treasury_level": {"type": "number"},
                    "event_type": {"type": "string"},
                    "action_taken": {"type": "string"},
                    "outcome": {"type": "boolean"}
                },
                "required": ["operation"]
            }
        }
    
    async def execute(self, call: ToolCall) -> Dict[str, Any]:
        operation = call.arguments["operation"]
        
        if operation == "query_survival":
            treasury_level = call.arguments.get("treasury_level", 0)
            memories = self.memory.get_survival_strategies(treasury_level)
            return {"memories": memories}
        
        elif operation == "record_survival":
            self.memory.record_survival_event(
                event_type=call.arguments["event_type"],
                treasury_level=call.arguments["treasury_level"],
                action_taken=call.arguments["action_taken"],
                outcome=call.arguments["outcome"]
            )
            return {"status": "recorded"}
        
        return {"error": "Unknown operation"}

class TreasuryTool(Tool):
    """MCP Tool for treasury operations"""
    
    def __init__(self, treasury_manager: TreasuryManager):
        self.treasury = treasury_manager
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "treasury",
            "description": "Manage agent's financial state and survival metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["get_state", "deduct_cost", "add_revenue", "get_survival_status"]
                    },
                    "amount": {"type": "number"},
                    "reason": {"type": "string"},
                    "source": {"type": "string"}
                },
                "required": ["operation"]
            }
        }
    
    async def execute(self, call: ToolCall) -> Dict[str, Any]:
        operation = call.arguments["operation"]
        
        if operation == "get_state":
            return self.treasury.get_agent_state()
        
        elif operation == "deduct_cost":
            self.treasury.deduct_cost(
                amount=call.arguments["amount"],
                reason=call.arguments["reason"]
            )
            return {"status": "deducted"}
        
        elif operation == "add_revenue":
            self.treasury.add_revenue(
                amount=call.arguments["amount"],
                source=call.arguments["source"]
            )
            return {"status": "added"}
        
        elif operation == "get_survival_status":
            return {"status": self.treasury.get_survival_status()}
        
        return {"error": "Unknown operation"}

class MarketTool(Tool):
    """MCP Tool for market operations"""
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "market",
            "description": "Get market data and yield opportunities",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["get_yield_opportunities", "get_market_condition", "get_gas_price"]
                    },
                    "protocol": {"type": "string"},
                    "amount": {"type": "number"}
                },
                "required": ["operation"]
            }
        }
    
    async def execute(self, call: ToolCall) -> Dict[str, Any]:
        operation = call.arguments["operation"]
        
        if operation == "get_yield_opportunities":
            # Simulate market data
            return {
                "opportunities": [
                    {"protocol": "aave", "apy": 0.05, "risk": "low"},
                    {"protocol": "compound", "apy": 0.08, "risk": "medium"},
                    {"protocol": "curve", "apy": 0.12, "risk": "high"}
                ]
            }
        
        elif operation == "get_market_condition":
            return {"condition": "stable", "volatility": 0.3}
        
        elif operation == "get_gas_price":
            return {"gas_price": 15.0, "unit": "gwei"}
        
        return {"error": "Unknown operation"}

class DecisionTool(Tool):
    """MCP Tool for making decisions"""
    
    def __init__(self, memory_tool: MemoryTool, treasury_tool: TreasuryTool, market_tool: MarketTool, base_tool: BaseBlockchainTool, mem0_tool: Mem0Tool):
        self.memory = memory_tool
        self.treasury = treasury_tool
        self.market = market_tool
        self.base = base_tool
        self.mem0 = mem0_tool
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "decision",
            "description": "Make a decision based on current context and memories",
            "parameters": {
                "type": "object",
                "properties": {
                    "context": {
                        "type": "object",
                        "properties": {
                            "current_treasury": {"type": "number"},
                            "market_condition": {"type": "string"},
                            "available_protocols": {"type": "array", "items": {"type": "string"}},
                            "gas_price": {"type": "number"},
                            "agent_address": {"type": "string"}
                        }
                    }
                },
                "required": ["context"]
            }
        }
    
    async def execute(self, call: ToolCall) -> Dict[str, Any]:
        context = call.arguments["context"]
        
        # Get current state from all tools
        treasury_state = await self.treasury.execute(ToolCall("get_state", {}))
        market_data = await self.market.execute(ToolCall("get_market_condition", {}))
        memories = await self.memory.execute(ToolCall("query_survival", {
            "treasury_level": context["current_treasury"]
        }))
        
        # Get blockchain state
        if "agent_address" in context:
            balance_data = await self.base.execute(ToolCall("get_balance", {
                "address": context["agent_address"]
            }))
        else:
            balance_data = {"balance": "0"}
        
        # Store decision context in Mem0
        decision_context = {
            "timestamp": str(asyncio.get_event_loop().time()),
            "treasury_state": treasury_state,
            "market_data": market_data,
            "blockchain_balance": balance_data,
            "memories": memories
        }
        
        await self.mem0.execute(ToolCall("store_memory", {
            "key": f"decision_{int(asyncio.get_event_loop().time())}",
            "value": decision_context,
            "metadata": {"type": "decision_context", "treasury_level": context["current_treasury"]}
        }))
        
        # Make decision based on state
        if treasury_state["survival_status"] == "CRITICAL":
            return {
                "action": "HOLD",
                "reasoning": "Treasury too low for active trading",
                "risk_score": 0.1,
                "confidence": 0.9,
                "blockchain_balance": balance_data
            }
        
        elif treasury_state["survival_status"] == "WARNING":
            return {
                "action": "CONSERVATIVE_YIELD",
                "protocol": "aave",
                "amount": context["current_treasury"] * 0.3,
                "reasoning": "Using proven safe strategy",
                "risk_score": 0.3,
                "confidence": 0.7,
                "blockchain_balance": balance_data
            }
        
        else:
            return {
                "action": "AGGRESSIVE_YIELD",
                "protocol": "compound",
                "amount": context["current_treasury"] * 0.6,
                "reasoning": "Treasury healthy, pursuing higher yields",
                "risk_score": 0.6,
                "confidence": 0.8,
                "blockchain_balance": balance_data
            } 