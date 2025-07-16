#!/usr/bin/env python3.11
"""Test Mem0 directly with the API key"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🧠 Testing Mem0 Direct Connection\n")

# Check API key
api_key = os.getenv("MEM0_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"API Key prefix: {api_key[:10]}...")

try:
    from mem0 import MemoryClient
    print("✅ mem0 imported successfully")
    
    # Initialize Mem0 client
    print("\n🔧 Initializing Mem0 client...")
    client = MemoryClient(api_key=api_key)
    print("✅ Mem0 client created")
    
    # Test adding a memory
    print("\n📝 Adding test memory...")
    result = client.add(
        messages=[{"role": "user", "content": "Testing Mem0 integration with Athena agent on BASE mainnet"}],
        user_id="athena-test-direct"
    )
    print(f"✅ Memory added: {result}")
    
    # Test searching memories
    print("\n🔍 Searching memories...")
    memories = client.search(
        query="Athena agent",
        user_id="athena-test-direct"
    )
    print(f"✅ Found {len(memories)} memories")
    for i, memory in enumerate(memories[:3]):
        print(f"   {i+1}. {memory.get('memory', memory.get('text', 'No content'))[:100]}...")
    
    # Test getting all memories
    print("\n📚 Getting all memories...")
    all_memories = client.get_all(user_id="athena-test-direct")
    print(f"✅ Total memories for user: {len(all_memories)}")
    
    print("\n🎉 Mem0 is working correctly!")
    
except Exception as e:
    print(f"❌ Error with Mem0: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Check if it's an API key issue
    if "api_key" in str(e).lower() or "authentication" in str(e).lower():
        print("\n💡 This appears to be an API key issue.")
        print("Please check:")
        print("1. Your Mem0 API key is correct")
        print("2. Your Mem0 account has sufficient credits")
        print("3. The API key has the right permissions")