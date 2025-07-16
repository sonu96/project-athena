#!/usr/bin/env python3.11
"""Test memory formation in the Athena agent"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Add src to path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integrations.mem0_cloud import Mem0CloudClient

async def test_memory_formation():
    """Test memory formation and retrieval"""
    print("🧠 Testing Memory Formation\n")
    
    # Create memory client
    client = Mem0CloudClient(user_id="athena-test")
    status = client.get_status()
    
    print(f"Client Status:")
    print(f"  Connected: {status['connected']}")
    print(f"  Simulation Mode: {status['simulation_mode']}")
    print(f"  User ID: {status['user_id']}")
    print(f"  Mem0 Available: {status['mem0_available']}")
    
    # Test memory operations
    print(f"\n📝 Testing memory operations...")
    
    # Add some test memories
    memories_to_add = [
        ("Athena agent successfully connected to BASE mainnet", "connection"),
        ("USDC/ETH pool observed with high volume", "market"),
        ("Gas prices are optimal for transactions", "gas"),
        ("Emotional state transitioned from stable to confident", "emotion"),
        ("CDP AgentKit integration working correctly", "technical")
    ]
    
    memory_ids = []
    for content, category in memories_to_add:
        memory_id = await client.add_memory(content=content, category=category)
        if memory_id:
            memory_ids.append(memory_id)
            print(f"  ✅ Added: {category} memory")
        else:
            print(f"  ⚠️  Failed to add: {category} memory")
    
    print(f"\n🔍 Testing memory search...")
    
    # Search for different types of memories
    search_queries = [
        "BASE mainnet",
        "USDC ETH",
        "gas prices",
        "emotional state",
        "CDP"
    ]
    
    for query in search_queries:
        results = await client.search_memories(query=query, limit=3)
        print(f"  Query '{query}': Found {len(results)} memories")
        for i, memory in enumerate(results[:2]):
            print(f"    {i+1}. {memory['content'][:60]}...")
    
    # Get memory statistics
    print(f"\n📊 Memory Statistics:")
    stats = await client.get_memory_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n✅ Memory formation test complete!")
    
    if status['simulation_mode']:
        print(f"\n💡 Note: Currently running in simulation mode.")
        print(f"To use real Mem0 storage:")
        print(f"1. Get a valid API key from https://app.mem0.ai/dashboard/api-keys")
        print(f"2. Update MEM0_API_KEY in your .env file")
        print(f"3. Restart the agent")

if __name__ == "__main__":
    asyncio.run(test_memory_formation())