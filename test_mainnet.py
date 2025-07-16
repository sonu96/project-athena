#!/usr/bin/env python3
"""Test script for running Athena agent on BASE mainnet"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.agent import AthenaAgent
from src.data.bigquery_client import BigQueryClient
from src.integrations.mem0_cloud import Mem0CloudClient
from src.workflows.cognitive_loop import create_cognitive_workflow
from src.workflows.state import ConsciousnessState

# Load environment variables
load_dotenv()

# Configuration for mainnet testing
MAINNET_CONFIG = {
    "NETWORK_ID": "8453",  # BASE mainnet
    "NETWORK_NAME": "base",
    "AERODROME_ROUTER": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
    "AERODROME_FACTORY": "0x420DD381b31aEf6683db6B902084cB0FFECe40Da",
    "USDC_ADDRESS": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "WETH_ADDRESS": "0x4200000000000000000000000000000000000006",
    "OBSERVATION_MODE": True,  # V1 only observes
    "CYCLE_INTERVAL": 300,  # 5 minutes for testing
}

async def test_mainnet_connection():
    """Test connection to BASE mainnet and verify all systems"""
    print("\n🚀 Starting Athena Agent Mainnet Test\n")
    
    try:
        # Initialize agent
        print("1. Initializing Athena agent...")
        agent = AthenaAgent(
            agent_id=os.getenv("AGENT_ID", "athena-mainnet-test"),
            network=MAINNET_CONFIG["NETWORK_NAME"],
            config=MAINNET_CONFIG
        )
        
        # Test CDP connection
        print("\n2. Testing CDP AgentKit connection to BASE mainnet...")
        wallet_address = await agent.get_wallet_address()
        print(f"   ✅ Wallet connected: {wallet_address}")
        
        # Check wallet balance
        balance = await agent.get_balance()
        print(f"   💰 Wallet balance: {balance} ETH")
        
        # Test BigQuery connection
        print("\n3. Testing BigQuery connection...")
        bq_client = BigQueryClient()
        
        # Create test observation
        test_observation = {
            "timestamp": datetime.utcnow(),
            "agent_id": agent.agent_id,
            "pool_address": "0x1234567890abcdef",  # Test pool
            "pool_type": "USDC/WETH",
            "tvl_usd": 1000000.0,
            "volume_24h_usd": 50000.0,
            "fee_apy": 0.05,
            "reward_apy": 0.10,
            "observation_notes": "Mainnet test observation"
        }
        
        # Store observation
        await bq_client.store_pool_observation(test_observation)
        print("   ✅ BigQuery write successful")
        
        # Query recent observations
        recent_obs = await bq_client.get_recent_observations(limit=5)
        print(f"   📊 Found {len(recent_obs)} recent observations")
        
        # Test Mem0 connection
        print("\n4. Testing Mem0 memory system...")
        memory_client = Mem0CloudClient()
        
        # Create test memory
        test_memory = await memory_client.add_memory(
            f"Mainnet test at {datetime.utcnow().isoformat()}. Wallet: {wallet_address}",
            user_id=agent.agent_id,
            metadata={
                "category": "system",
                "type": "test",
                "network": "base-mainnet"
            }
        )
        print("   ✅ Memory created successfully")
        
        # Search memories
        memories = await memory_client.search_memories(
            query="mainnet test",
            user_id=agent.agent_id,
            limit=5
        )
        print(f"   🧠 Found {len(memories)} related memories")
        
        # Test Aerodrome pool observation
        print("\n5. Testing Aerodrome pool observation...")
        
        # Get top pools
        print("   Fetching top Aerodrome pools...")
        pools = await agent.observe_top_pools(limit=5)
        
        if pools:
            print(f"   ✅ Found {len(pools)} active pools:")
            for pool in pools[:3]:  # Show top 3
                print(f"      - {pool['symbol']}: TVL ${pool['tvl_usd']:,.2f}, APY {pool['total_apy']:.2%}")
        else:
            print("   ⚠️  No pools found (might need to implement pool fetching)")
        
        # Run one cognitive cycle
        print("\n6. Running cognitive cycle...")
        
        # Create workflow
        workflow = create_cognitive_workflow()
        
        # Initial state
        initial_state = ConsciousnessState(
            agent_id=agent.agent_id,
            timestamp=datetime.utcnow(),
            cycle_count=1,
            treasury_balance=100.0,  # Test treasury
            wallet_address=wallet_address,
            network=MAINNET_CONFIG["NETWORK_NAME"]
        )
        
        # Run cycle
        print("   Starting cognitive loop...")
        result = await workflow.ainvoke(initial_state)
        
        print("   ✅ Cognitive cycle completed")
        print(f"   Emotional state: {result['emotional_state']}")
        print(f"   Memories formed: {len(result.get('memories_formed', []))}")
        print(f"   Total cost: ${result.get('total_cost', 0):.4f}")
        
        # Store agent metrics
        print("\n7. Storing agent metrics...")
        metrics = {
            "timestamp": datetime.utcnow(),
            "agent_id": agent.agent_id,
            "treasury_balance": result['treasury_balance'],
            "emotional_state": result['emotional_state'],
            "cycle_count": result['cycle_count'],
            "memories_formed": len(result.get('memories_formed', [])),
            "patterns_recognized": len(result.get('active_patterns', [])),
            "total_cost": result.get('total_cost', 0),
            "cost_per_decision": result.get('total_cost', 0) / max(1, result['cycle_count'])
        }
        
        await bq_client.store_agent_metrics(metrics)
        print("   ✅ Metrics stored in BigQuery")
        
        print("\n✅ All systems operational! Ready for 24/7 deployment.")
        
        # Summary
        print("\n📊 Test Summary:")
        print(f"   - Network: BASE Mainnet (Chain ID: {MAINNET_CONFIG['NETWORK_ID']})")
        print(f"   - Wallet: {wallet_address}")
        print(f"   - Balance: {balance} ETH")
        print(f"   - BigQuery: Connected")
        print(f"   - Mem0: Connected")
        print(f"   - Emotional State: {result['emotional_state']}")
        print(f"   - Ready for Production: YES")
        
    except Exception as e:
        print(f"\n❌ Error during mainnet test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def continuous_test(duration_minutes=10):
    """Run continuous test for specified duration"""
    print(f"\n🔄 Running continuous test for {duration_minutes} minutes...")
    
    agent = AthenaAgent(
        agent_id=os.getenv("AGENT_ID", "athena-mainnet-continuous"),
        network=MAINNET_CONFIG["NETWORK_NAME"],
        config=MAINNET_CONFIG
    )
    
    workflow = create_cognitive_workflow()
    start_time = datetime.utcnow()
    cycle_count = 0
    
    while (datetime.utcnow() - start_time).total_seconds() < duration_minutes * 60:
        cycle_count += 1
        print(f"\n--- Cycle {cycle_count} at {datetime.utcnow().isoformat()} ---")
        
        try:
            # Get current state
            state = ConsciousnessState(
                agent_id=agent.agent_id,
                timestamp=datetime.utcnow(),
                cycle_count=cycle_count,
                treasury_balance=100.0 - (cycle_count * 0.1),  # Simulate spending
                wallet_address=await agent.get_wallet_address(),
                network=MAINNET_CONFIG["NETWORK_NAME"]
            )
            
            # Run cycle
            result = await workflow.ainvoke(state)
            
            print(f"✅ Cycle completed: {result['emotional_state']}, Cost: ${result.get('total_cost', 0):.4f}")
            
            # Wait before next cycle
            await asyncio.sleep(MAINNET_CONFIG["CYCLE_INTERVAL"])
            
        except Exception as e:
            print(f"❌ Error in cycle {cycle_count}: {e}")
            await asyncio.sleep(30)  # Wait before retry
    
    print(f"\n✅ Continuous test completed: {cycle_count} cycles in {duration_minutes} minutes")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Athena agent on BASE mainnet")
    parser.add_argument("--continuous", type=int, help="Run continuous test for N minutes")
    args = parser.parse_args()
    
    if args.continuous:
        asyncio.run(continuous_test(args.continuous))
    else:
        asyncio.run(test_mainnet_connection())