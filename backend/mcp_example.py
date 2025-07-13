"""
MCP DeFi Agent Example with Base Blockchain and Mem0 Integration

This example demonstrates how to use the MCP tools to:
1. Connect to Base blockchain for DeFi operations
2. Use Mem0 for persistent memory storage
3. Make decisions based on blockchain state and historical memories
4. Execute transactions and record experiences
"""

import asyncio
import os
from typing import Dict, Any
from .mcp_agent import MCPAgentAPI
from .models import DecisionContext

async def main():
    """Example usage of MCP DeFi Agent with Base and Mem0"""
    
    # Initialize the MCP agent
    agent_api = MCPAgentAPI()
    
    # Example 1: Get blockchain balance
    print("=== Getting Blockchain Balance ===")
    agent_address = os.getenv("AGENT_ADDRESS", "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6")
    balance = await agent_api.get_blockchain_balance(agent_address)
    print(f"Agent balance: {balance}")
    
    # Example 2: Search historical memories
    print("\n=== Searching Historical Memories ===")
    memories = await agent_api.search_memories(
        query="yield farming strategies during low treasury",
        memory_type="strategy"
    )
    print(f"Found memories: {memories}")
    
    # Example 3: Make a decision with blockchain context
    print("\n=== Making Decision with Blockchain Context ===")
    context = DecisionContext(
        current_treasury=1000.0,
        market_condition="stable",
        available_protocols=["aave", "compound", "curve"],
        gas_price=15.0,
        agent_address=agent_address
    )
    
    decision = await agent_api.make_decision(context)
    print(f"Decision: {decision.action}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Blockchain balance: {decision.blockchain_balance}")
    
    # Example 4: Record experience with blockchain data
    print("\n=== Recording Experience ===")
    experience = {
        "event_type": "yield_farming_attempt",
        "treasury_level": 1000.0,
        "action_taken": decision.action,
        "outcome": True,
        "blockchain_balance": decision.blockchain_balance,
        "gas_used": 150000,
        "transaction_hash": "0x1234567890abcdef"
    }
    
    await agent_api.record_experience(experience)
    print("Experience recorded in both local and persistent memory")
    
    # Example 5: Execute blockchain transaction
    print("\n=== Executing Blockchain Transaction ===")
    if decision.action != "HOLD":
        # Simulate token approval
        approval_result = await agent_api.execute_blockchain_transaction(
            operation="approve_token",
            token_address="0xA0b86a33E6441b8c4C8C0C8C0C8C0C8C0C8C0C8C",
            spender_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
            amount=1000000000000000000  # 1 token with 18 decimals
        )
        print(f"Approval result: {approval_result}")
    
    # Example 6: Get comprehensive agent state
    print("\n=== Getting Agent State ===")
    state = await agent_api.get_state()
    print(f"Treasury: {state['treasury']}")
    print(f"Market: {state['market']}")
    print(f"Blockchain: {state['blockchain']}")
    
    # Example 7: Simulate cost and check survival
    print("\n=== Simulating Cost ===")
    await agent_api.simulate_cost(amount=0.05, reason="gas_fee_for_yield_farming")
    
    # Example 8: Get yield opportunities
    print("\n=== Getting Yield Opportunities ===")
    opportunities = await agent_api.get_yield_opportunities()
    print(f"Available opportunities: {opportunities}")

async def advanced_example():
    """Advanced example showing complex DeFi operations"""
    
    agent_api = MCPAgentAPI()
    
    print("=== Advanced DeFi Operations ===")
    
    # 1. Check multiple token balances
    tokens = [
        "0xA0b86a33E6441b8c4C8C0C8C0C8C0C8C0C8C0C8C",  # USDC
        "0x4200000000000000000000000000000000000006",  # WETH
        "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"   # USDbC
    ]
    
    for token in tokens:
        balance = await agent_api.execute_blockchain_transaction(
            operation="get_contract_balance",
            token_address=token,
            address=os.getenv("AGENT_ADDRESS")
        )
        print(f"Token {token}: {balance}")
    
    # 2. Search for specific memory patterns
    memory_patterns = [
        "successful yield farming with high gas prices",
        "failed transactions due to insufficient balance",
        "profitable arbitrage opportunities"
    ]
    
    for pattern in memory_patterns:
        memories = await agent_api.search_memories(pattern, "experience")
        print(f"Pattern '{pattern}': {len(memories.get('results', []))} memories found")
    
    # 3. Simulate complex decision making
    scenarios = [
        {"treasury": 100, "market": "volatile", "gas_price": 50},
        {"treasury": 1000, "market": "stable", "gas_price": 15},
        {"treasury": 10000, "market": "bullish", "gas_price": 10}
    ]
    
    for scenario in scenarios:
        context = DecisionContext(
            current_treasury=scenario["treasury"],
            market_condition=scenario["market"],
            available_protocols=["aave", "compound", "curve"],
            gas_price=scenario["gas_price"],
            agent_address=os.getenv("AGENT_ADDRESS")
        )
        
        decision = await agent_api.make_decision(context)
        print(f"Scenario {scenario}: {decision.action} (confidence: {decision.confidence})")

if __name__ == "__main__":
    # Run basic example
    asyncio.run(main())
    
    # Run advanced example
    asyncio.run(advanced_example()) 