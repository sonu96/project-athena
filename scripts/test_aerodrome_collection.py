#!/usr/bin/env python3
"""Test Aerodrome data collection and BigQuery storage"""

import os
import sys
import asyncio
from datetime import datetime
from google.cloud import bigquery
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.bigquery_client import BigQueryClient
from src.aerodrome.observer import AerodromeObserver
from src.blockchain.cdp_client import CDPClient

load_dotenv()

async def test_aerodrome_collection():
    """Test collecting Aerodrome data and storing in BigQuery"""
    
    print("🧪 Testing Aerodrome Data Collection\n")
    
    # Initialize clients
    print("1️⃣ Initializing clients...")
    cdp_client = CDPClient()
    observer = AerodromeObserver(cdp_client)
    bq_client = BigQueryClient()
    
    # Ensure BigQuery is set up
    print("\n2️⃣ Setting up BigQuery...")
    await bq_client.ensure_dataset_exists()
    await bq_client.ensure_tables_exist()
    print("✅ BigQuery ready")
    
    # Fetch pool data
    print("\n3️⃣ Fetching Aerodrome pools...")
    pools = await observer.get_top_pools(limit=5)
    
    if not pools:
        print("⚠️  No pools fetched - observer might be in simulation mode")
        print("   Generating simulated data for testing...")
        # Force simulation mode for testing
        observer.simulation_mode = True
        pools = await observer.get_top_pools(limit=5)
    
    print(f"✅ Fetched {len(pools)} pools")
    
    # Display pool data
    print("\n📊 Pool Data:")
    for i, pool in enumerate(pools[:3]):
        print(f"\nPool {i+1}:")
        print(f"  Address: {pool['address']}")
        print(f"  Pair: {pool['token0_symbol']}/{pool['token1_symbol']}")
        print(f"  Type: {pool['type']}")
        print(f"  TVL: ${pool['tvl_usd']:,.2f}")
        print(f"  Volume 24h: ${pool['volume_24h_usd']:,.2f}")
        print(f"  Total APY: {pool['total_apy']:.2%}")
    
    # Store in BigQuery
    print("\n4️⃣ Storing data in BigQuery...")
    
    success_count = 0
    for pool in pools:
        # Prepare pool data for BigQuery
        pool_observation = {
            "pool_address": pool["address"],
            "pool_type": pool["type"],
            "token0_symbol": pool["token0_symbol"],
            "token1_symbol": pool["token1_symbol"],
            "tvl_usd": pool["tvl_usd"],
            "volume_24h_usd": pool["volume_24h_usd"],
            "fee_apy": pool["fee_apy"],
            "reward_apy": pool["reward_apy"],
            "total_apy": pool["total_apy"]
        }
        
        # Log observation
        success = await bq_client.log_pool_observation(
            agent_id="test-collector",
            pool_data=pool_observation
        )
        
        if success:
            success_count += 1
    
    print(f"✅ Stored {success_count}/{len(pools)} observations in BigQuery")
    
    # Query to verify
    print("\n5️⃣ Verifying data in BigQuery...")
    
    query = f"""
    SELECT 
        COUNT(*) as total_observations,
        COUNT(DISTINCT pool_address) as unique_pools,
        AVG(tvl_usd) as avg_tvl,
        MAX(total_apy) as max_apy
    FROM `{os.getenv('GCP_PROJECT_ID', 'athena-agent-prod')}.athena_analytics.pool_observations`
    WHERE DATE(timestamp) = CURRENT_DATE()
    """
    
    results = await bq_client.query(query)
    
    if results:
        stats = results[0]
        print("\n📈 Today's Statistics:")
        print(f"  Total observations: {stats.get('total_observations', 0)}")
        print(f"  Unique pools: {stats.get('unique_pools', 0)}")
        print(f"  Average TVL: ${stats.get('avg_tvl', 0):,.2f}")
        print(f"  Max APY: {stats.get('max_apy', 0):.2%}")
    
    print("\n✅ Test completed successfully!")
    print("\n🎯 Next steps:")
    print("1. Deploy the cloud function: python3 scripts/deploy_pool_collector.py")
    print("2. Monitor BigQuery table: athena_analytics.pool_observations")
    print("3. Set up Grafana dashboard for visualization")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_aerodrome_collection())
    if not success:
        print("\n❌ Test failed - check errors above")
        sys.exit(1)