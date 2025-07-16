#!/usr/bin/env python3
"""
Test script to verify Athena Agent setup
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

async def test_imports():
    """Test all imports"""
    print("Testing imports...")
    
    try:
        from src.core import AthenaAgent, ConsciousnessState, EmotionalState
        print("✅ Core imports successful")
        
        from src.workflows import create_cognitive_workflow
        print("✅ Workflow imports successful")
        
        from src.blockchain import CDPClient
        print("✅ Blockchain imports successful")
        
        from src.memory import MemoryClient
        print("✅ Memory imports successful")
        
        from src.database import FirestoreClient, BigQueryClient
        print("✅ Database imports successful")
        
        from src.api import create_app
        print("✅ API imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


async def test_configuration():
    """Test configuration"""
    print("\nTesting configuration...")
    
    try:
        from src.config import settings
        
        print(f"✅ Agent ID: {settings.agent_id}")
        print(f"✅ Network: {settings.network}")
        print(f"✅ Starting treasury: ${settings.starting_treasury}")
        
        # Check required keys (without revealing them)
        if settings.cdp_api_key_name:
            print("✅ CDP API key configured")
        else:
            print("❌ CDP API key missing")
            
        if settings.mem0_api_key:
            print("✅ Mem0 API key configured")
        else:
            print("❌ Mem0 API key missing")
            
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


async def test_consciousness():
    """Test consciousness state"""
    print("\nTesting consciousness state...")
    
    try:
        from src.core.consciousness import ConsciousnessState
        from src.core.emotions import EmotionalState
        
        state = ConsciousnessState(
            agent_id="test",
            treasury_balance=100.0,
            emotional_state=EmotionalState.STABLE
        )
        
        print(f"✅ Created consciousness state")
        print(f"   Treasury: ${state.treasury_balance}")
        print(f"   Emotional state: {state.emotional_state.value}")
        print(f"   Observation frequency: {state.get_observation_frequency_minutes()} minutes")
        
        return True
        
    except Exception as e:
        print(f"❌ Consciousness error: {e}")
        return False


async def test_cdp_simulation():
    """Test CDP in simulation mode"""
    print("\nTesting CDP client (simulation)...")
    
    try:
        from src.blockchain import CDPClient
        
        cdp = CDPClient()
        balance = await cdp.get_wallet_balance()
        gas_price = await cdp.get_gas_price()
        
        print(f"✅ CDP simulation working")
        print(f"   Balance: ${balance:.2f}")
        print(f"   Gas price: {gas_price:.1f} gwei")
        
        return True
        
    except Exception as e:
        print(f"❌ CDP error: {e}")
        return False


async def main():
    """Run all tests"""
    print("🏛️ Athena Agent Setup Test\n")
    
    tests = [
        test_imports(),
        test_configuration(),
        test_consciousness(),
        test_cdp_simulation()
    ]
    
    results = await asyncio.gather(*tests)
    
    if all(results):
        print("\n✅ All tests passed! Agent is ready to run.")
        print("\nTo start the agent:")
        print("  python -m src.core.agent")
        print("\nTo start with API:")
        print("  python scripts/run_with_api.py")
    else:
        print("\n❌ Some tests failed. Please check your setup.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())