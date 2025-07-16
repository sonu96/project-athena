#!/usr/bin/env python3.11
"""Test LangSmith tracing integration"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.monitoring.langsmith_config import configure_langsmith

def test_langsmith_setup():
    """Test LangSmith configuration"""
    print("🔍 Testing LangSmith Configuration\n")
    
    # Check environment variables
    print("1. Checking environment variables...")
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT")
    
    print(f"   LANGSMITH_API_KEY: {'✅ Set' if api_key else '❌ Missing'}")
    if api_key:
        print(f"   API Key prefix: {api_key[:15]}...")
    
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
    
    # Test a simple LangChain operation with tracing
    print(f"\n4. Testing LangChain operation with tracing...")
    
    try:
        from langchain_core.messages import HumanMessage
        from langchain_google_vertexai import ChatVertexAI
        
        # Create a simple LLM call that should be traced
        llm = ChatVertexAI(
            model_name="gemini-1.5-flash-002",
            project=os.getenv("GOOGLE_VERTEX_PROJECT"),
            location=os.getenv("GOOGLE_VERTEX_LOCATION")
        )
        
        print(f"   ✅ LLM initialized")
        
        # Make a traced call
        message = HumanMessage(content="Hello, this is a test for LangSmith tracing from Athena agent. Please respond with 'Tracing test successful!'")
        
        print(f"   📡 Making traced LLM call...")
        response = llm.invoke([message])
        
        print(f"   ✅ LLM Response: {response.content}")
        print(f"   📊 This call should appear in LangSmith console")
        
    except Exception as e:
        print(f"   ❌ LLM test failed: {e}")
    
    # Test with LangGraph workflow
    print(f"\n5. Testing LangGraph workflow tracing...")
    
    try:
        from langgraph.graph import StateGraph, END
        from typing import TypedDict
        
        class SimpleState(TypedDict):
            messages: list
            
        def simple_node(state: SimpleState):
            """Simple node for testing"""
            return {"messages": state["messages"] + ["LangGraph node executed"]}
        
        # Create a simple workflow
        workflow = StateGraph(SimpleState)
        workflow.add_node("test_node", simple_node)
        workflow.set_entry_point("test_node")
        workflow.add_edge("test_node", END)
        
        app = workflow.compile()
        
        print(f"   ✅ LangGraph workflow created")
        
        # Execute workflow (this should be traced)
        result = app.invoke({"messages": ["Starting LangGraph test"]})
        
        print(f"   ✅ Workflow executed: {result}")
        print(f"   📊 This workflow should appear in LangSmith console")
        
    except Exception as e:
        print(f"   ❌ LangGraph test failed: {e}")
    
    print(f"\n✅ LangSmith testing complete!")
    print(f"\n💡 Check your LangSmith console at:")
    print(f"   https://smith.langchain.com/projects")
    print(f"   Project: {langchain_project}")

if __name__ == "__main__":
    test_langsmith_setup()