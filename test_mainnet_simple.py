#!/usr/bin/env python3
"""Simple test script for BASE mainnet connection"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration for mainnet
MAINNET_CONFIG = {
    "NETWORK_ID": "8453",  # BASE mainnet
    "NETWORK_NAME": "base",
    "AERODROME_ROUTER": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
    "AERODROME_FACTORY": "0x420DD381b31aEf6683db6B902084cB0FFECe40Da",
    "USDC_ADDRESS": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "WETH_ADDRESS": "0x4200000000000000000000000000000000000006",
}

async def test_basic_setup():
    """Test basic environment setup"""
    print("\n🚀 Testing Athena Agent Setup for BASE Mainnet\n")
    
    # Check environment variables
    print("1. Environment Variables:")
    required_vars = ["AGENT_ID", "CDP_API_KEY_NAME", "CDP_API_KEY_SECRET", "MEM0_API_KEY"]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * 8}{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"   ❌ {var}: Not set")
    
    # Test imports
    print("\n2. Testing Core Imports:")
    try:
        from src.core.agent import AthenaAgent
        print("   ✅ AthenaAgent imported")
    except ImportError as e:
        print(f"   ❌ Failed to import AthenaAgent: {e}")
        return False
    
    try:
        from src.memory.client import MemoryClient
        print("   ✅ MemoryClient imported")
    except ImportError as e:
        print(f"   ❌ Failed to import MemoryClient: {e}")
    
    try:
        from src.workflows.cognitive_loop import create_cognitive_workflow
        print("   ✅ Cognitive workflow imported")
    except ImportError as e:
        print(f"   ❌ Failed to import cognitive workflow: {e}")
    
    # Test agent initialization
    print("\n3. Initializing Agent:")
    try:
        agent = AthenaAgent()
        print("   ✅ Agent created")
        print(f"   🤖 Agent ID: {agent.agent_id}")
        
        # Get wallet info
        wallet_address = agent.wallet_manager.get_address()
        print(f"   💳 Wallet: {wallet_address}")
        print(f"   🌐 Network: BASE Mainnet (Chain ID: {MAINNET_CONFIG['NETWORK_ID']})")
        
    except Exception as e:
        print(f"   ❌ Failed to create agent: {e}")
        return False
    
    # Test memory system
    print("\n4. Testing Memory System:")
    try:
        memory_client = MemoryClient()
        
        # Add test memory
        test_memory = await memory_client.add(
            content=f"Test connection at {datetime.utcnow().isoformat()}",
            metadata={"type": "test", "network": "base-mainnet"}
        )
        print("   ✅ Memory system connected")
        
        # Search memories
        memories = await memory_client.search(
            query="test",
            limit=1
        )
        print(f"   🧠 Found {len(memories)} memories")
        
    except Exception as e:
        print(f"   ❌ Memory system error: {e}")
    
    # Test workflow
    print("\n5. Testing Cognitive Workflow:")
    try:
        from src.workflows.state import ConsciousnessState
        
        # Create initial state
        state = ConsciousnessState(
            agent_id=agent.agent_id,
            timestamp=datetime.utcnow(),
            cycle_count=1,
            treasury_balance=100.0,
            wallet_address=wallet_address,
            network=MAINNET_CONFIG["NETWORK_NAME"]
        )
        print("   ✅ State created")
        
        # Create workflow
        workflow = create_cognitive_workflow()
        print("   ✅ Workflow created")
        
        # Test one step
        print("   Running test cycle...")
        result = await workflow.ainvoke(state)
        
        print(f"   ✅ Cycle completed")
        print(f"   Emotional state: {result.get('emotional_state', 'unknown')}")
        print(f"   Cost: ${result.get('total_cost', 0):.4f}")
        
    except Exception as e:
        print(f"   ❌ Workflow error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Basic setup test completed!")
    print("\n📋 Next Steps:")
    print("1. Ensure all environment variables are set correctly")
    print("2. Check that you have sufficient ETH in the wallet for gas")
    print("3. Run the full mainnet test: python test_mainnet.py")
    print("4. Deploy to Cloud Run for 24/7 operation: ./deploy_cloud.sh")
    
    return True

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_basic_setup())
    sys.exit(0 if success else 1)