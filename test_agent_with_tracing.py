#!/usr/bin/env python3.11
"""Test Athena agent with LangSmith tracing"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.agent import AthenaAgent
from src.workflows.state import ConsciousnessState
from src.core.emotions import EmotionalState

async def test_agent_with_tracing():
    """Test Athena agent cognitive cycle with LangSmith tracing"""
    print("🤖 Testing Athena Agent with LangSmith Tracing\n")
    
    try:
        # Initialize agent (this should configure LangSmith)
        print("1. Initializing Athena agent...")
        agent = AthenaAgent()
        print("   ✅ Agent initialized")
        
        # Create initial consciousness state
        print("\n2. Creating consciousness state...")
        initial_state = ConsciousnessState(
            agent_id="athena-langsmith-test",
            emotional_state=EmotionalState.STABLE,
            treasury_balance=100.0,
            market_data={
                "test_mode": True,
                "network": "base-mainnet",
                "timestamp": datetime.now().isoformat()
            }
        )
        print("   ✅ Consciousness state created")
        
        # Run a cognitive cycle (this should be traced)
        print("\n3. Running cognitive cycle with tracing...")
        print("   📡 Starting traced cognitive cycle...")
        
        # Import the cognitive loop
        from src.workflows.cognitive_loop import run_cognitive_cycle, create_cognitive_workflow
        
        # Create the workflow
        workflow = create_cognitive_workflow()
        
        # Run the cycle (this should create traces in LangSmith)
        result_state = await run_cognitive_cycle(workflow, initial_state)
        
        print("   ✅ Cognitive cycle completed!")
        print(f"   📊 Cycle count: {result_state.cycle_count}")
        print(f"   🎭 Emotional state: {result_state.emotional_state}")
        print(f"   💰 Treasury: ${result_state.treasury_balance}")
        print(f"   💸 Total cost: ${result_state.total_cost}")
        print(f"   🧠 Memories: {len(result_state.recent_memories)}")
        print(f"   📈 This cognitive cycle should appear in LangSmith!")
        
        # Run another cycle to generate more trace data
        print("\n4. Running second cycle for more trace data...")
        result_state.add_observation({
            "pool": "USDC/ETH",
            "tvl": 1500000,
            "volume_24h": 250000,
            "test_observation": True
        })
        
        second_result = await run_cognitive_cycle(workflow, result_state)
        
        print("   ✅ Second cycle completed!")
        print(f"   📊 Total cycles: {second_result.cycle_count}")
        print(f"   🎭 Emotional state: {second_result.emotional_state}")
        print(f"   📈 Both cycles should be visible in LangSmith!")
        
        # Summary
        print(f"\n✅ Agent tracing test complete!")
        print(f"\n📊 Summary:")
        print(f"   • Agent ID: {second_result.agent_id}")
        print(f"   • Cycles completed: {second_result.cycle_count}")
        print(f"   • Emotional state: {second_result.emotional_state.value}")
        print(f"   • Observations: {len(second_result.observed_pools)}")
        print(f"   • Memories formed: {len(second_result.recent_memories)}")
        print(f"   • Total cost: ${second_result.total_cost}")
        
        print(f"\n🌐 View traces in LangSmith:")
        print(f"   https://smith.langchain.com/projects")
        print(f"   Project: athena-mainnet-v1")
        print(f"   Look for runs with agent_id: athena-langsmith-test")
        
    except Exception as e:
        print(f"❌ Error during agent test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_with_tracing())