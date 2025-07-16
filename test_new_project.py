#!/usr/bin/env python3.11
"""Test Gemini API with the new Google Cloud project"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_new_gemini_project():
    """Test Gemini API with the new project"""
    print("🤖 Testing Gemini API with New Google Cloud Project\n")
    
    # Reset cost manager
    from src.monitoring.cost_manager import cost_manager
    cost_manager.daily_costs = cost_manager._create_fresh_costs()
    cost_manager.emergency_mode = False
    cost_manager.shutdown_triggered = False
    
    print("1. Project configuration:")
    print(f"   Project ID: {os.getenv('GOOGLE_VERTEX_PROJECT')}")
    print(f"   Location: {os.getenv('GOOGLE_VERTEX_LOCATION')}")
    print(f"   Starting budget: ${cost_manager.HARD_LIMIT}")
    
    print("\n2. Testing real Gemini API call...")
    
    try:
        from src.workflows.cost_aware_llm import cost_aware_llm
        from src.workflows.state import ConsciousnessState
        from src.core.emotions import EmotionalState
        from langchain_core.messages import HumanMessage
        
        # Create test state
        state = ConsciousnessState(
            agent_id="gemini-test",
            emotional_state=EmotionalState.STABLE,
            treasury_balance=100.0
        )
        
        # Test message
        messages = [
            HumanMessage(content="Hello! This is a test of the Athena agent's cost-managed Gemini integration. Please respond with: 'Gemini API working with cost protection!' and nothing else.")
        ]
        
        print("   🚀 Making real Gemini API call...")
        
        # Make the call
        response = await cost_aware_llm.generate_response(
            state=state,
            messages=messages,
            task_type="api_test"
        )
        
        if response:
            print(f"   ✅ SUCCESS! Gemini Response: {response}")
            
            # Check cost tracking
            cost_status = cost_aware_llm.get_cost_status()
            print(f"   💰 Cost tracked: ${cost_status['total_cost']:.6f}")
            print(f"   📊 Remaining budget: ${cost_manager.get_max_affordable_cost():.6f}")
            
        else:
            print(f"   ❌ No response received")
        
    except Exception as e:
        print(f"   ❌ Gemini API test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n3. Final status:")
    status = cost_manager.get_status()
    print(f"   Total spent: ${status['total_cost']:.6f}")
    print(f"   Emergency mode: {status['emergency_mode']}")
    print(f"   Shutdown triggered: {status['shutdown_triggered']}")
    
    if status['total_cost'] > 0:
        print(f"\n🎉 SUCCESS: Real Gemini API calls are working with cost protection!")
    else:
        print(f"\n⚠️  API calls may still be using mock models")

if __name__ == "__main__":
    asyncio.run(test_new_gemini_project())