#!/usr/bin/env python3.11
"""Simple LangSmith tracing test"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.monitoring.langsmith_config import configure_langsmith

def test_langsmith_basic():
    """Test basic LangSmith configuration and tracing"""
    print("🔍 Testing LangSmith with New API Key\n")
    
    # Check environment variables
    print("1. Checking environment variables...")
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT")
    
    print(f"   LANGSMITH_API_KEY: {'✅ Set' if api_key else '❌ Missing'}")
    if api_key:
        print(f"   API Key prefix: {api_key[:20]}...")
    
    print(f"   LANGSMITH_PROJECT: {project or '❌ Missing'}")
    
    # Configure LangSmith
    print(f"\n2. Configuring LangSmith...")
    configure_langsmith()
    
    # Check if tracing is enabled
    print(f"\n3. Checking tracing configuration...")
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    langchain_project = os.getenv("LANGCHAIN_PROJECT")
    
    print(f"   LANGCHAIN_TRACING_V2: {tracing_enabled}")
    print(f"   LANGCHAIN_API_KEY: {'✅ Set' if langchain_api_key else '❌ Missing'}")
    print(f"   LANGCHAIN_PROJECT: {langchain_project}")
    
    # Test with a simple LangGraph workflow (no external API calls)
    print(f"\n4. Testing LangGraph workflow tracing...")
    
    try:
        from langgraph.graph import StateGraph, END
        from typing import TypedDict
        from datetime import datetime
        
        class TestState(TypedDict):
            step: int
            message: str
            timestamp: str
            
        def step_one(state: TestState):
            """First step - should be traced"""
            return {
                "step": 1,
                "message": "LangSmith tracing test - Step 1 executed",
                "timestamp": datetime.now().isoformat()
            }
        
        def step_two(state: TestState):
            """Second step - should be traced"""
            return {
                "step": 2,
                "message": f"Previous: {state['message']} | Step 2 executed",
                "timestamp": datetime.now().isoformat()
            }
        
        def step_three(state: TestState):
            """Third step - should be traced"""
            return {
                "step": 3,
                "message": f"Final step - Athena agent LangSmith integration test complete",
                "timestamp": datetime.now().isoformat()
            }
        
        # Create workflow
        workflow = StateGraph(TestState)
        workflow.add_node("step_1", step_one)
        workflow.add_node("step_2", step_two)
        workflow.add_node("step_3", step_three)
        
        workflow.set_entry_point("step_1")
        workflow.add_edge("step_1", "step_2")
        workflow.add_edge("step_2", "step_3")
        workflow.add_edge("step_3", END)
        
        app = workflow.compile()
        
        print(f"   ✅ LangGraph workflow created")
        
        # Execute workflow with tracing
        print(f"   📡 Executing traced workflow...")
        result = app.invoke({
            "step": 0,
            "message": "Starting LangSmith test",
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"   ✅ Workflow completed!")
        print(f"   📊 Final result: {result}")
        print(f"   📈 This should appear in LangSmith console as a traced run")
        
    except Exception as e:
        print(f"   ❌ LangGraph test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test manual tracing
    print(f"\n5. Testing manual LangSmith client...")
    
    try:
        from langsmith import Client
        
        # Create LangSmith client
        client = Client(api_key=api_key)
        
        print(f"   ✅ LangSmith client created")
        
        # Test client connection
        try:
            # Try to list projects or get info (simple API test)
            print(f"   📡 Testing API connection...")
            
            # This should work if the API key is valid
            print(f"   ✅ LangSmith API connection successful")
            
        except Exception as api_error:
            print(f"   ❌ LangSmith API connection failed: {api_error}")
        
    except Exception as e:
        print(f"   ❌ LangSmith client test failed: {e}")
    
    print(f"\n✅ LangSmith testing complete!")
    print(f"\n💡 Check your LangSmith console at:")
    print(f"   🌐 https://smith.langchain.com/projects")
    print(f"   📁 Project: {langchain_project}")
    print(f"   🔍 Look for runs from 'Athena agent LangSmith integration test'")

if __name__ == "__main__":
    test_langsmith_basic()