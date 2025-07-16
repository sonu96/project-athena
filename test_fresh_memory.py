#!/usr/bin/env python3.11
"""Test adding a fresh memory to Mem0"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add src to path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integrations.mem0_cloud import Mem0CloudClient

async def test_fresh_memory():
    """Test adding a unique memory"""
    print("🧠 Testing Fresh Memory Addition\n")
    
    client = Mem0CloudClient(user_id="athena-production")
    
    # Create a unique memory with timestamp
    timestamp = datetime.now().isoformat()
    unique_content = f"Athena agent production test at {timestamp}. Testing real Mem0 integration with BASE mainnet configuration. CDP AgentKit authenticated successfully."
    
    print(f"📝 Adding unique memory...")
    memory_id = await client.add_memory(
        content=unique_content,
        category="production_test",
        metadata={
            "timestamp": timestamp,
            "test_type": "production_verification",
            "network": "base-mainnet"
        }
    )
    
    if memory_id:
        print(f"✅ Memory added successfully!")
        print(f"   Memory ID: {memory_id}")
        
        # Search for the memory
        print(f"\n🔍 Searching for the new memory...")
        results = await client.search_memories("production test", limit=5)
        print(f"   Found {len(results)} memories")
        
        for i, memory in enumerate(results):
            print(f"   {i+1}. {memory.get('content', memory.get('memory', 'No content'))[:80]}...")
        
        # Get all memories for this user
        print(f"\n📚 All memories for user:")
        stats = await client.get_memory_stats()
        print(f"   Total memories: {stats['total_memories']}")
        print(f"   Categories: {stats['categories']}")
        
    else:
        print(f"❌ Failed to add memory")
    
    print(f"\n✅ Fresh memory test complete!")

if __name__ == "__main__":
    asyncio.run(test_fresh_memory())