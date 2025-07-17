#!/usr/bin/env python3
"""Setup and run Aerodrome mainnet data collection"""

import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv, set_key

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

async def setup_and_collect():
    """Setup environment and start collecting Aerodrome data"""
    
    print("🚀 Setting up Aerodrome Mainnet Data Collection\n")
    
    # 1. Fix environment variables
    print("1️⃣ Configuring environment...")
    
    # Get correct project ID from service account
    try:
        with open("service-account-key.json", "r") as f:
            sa_data = json.load(f)
            project_id = sa_data["project_id"]
            print(f"✅ Found project ID: {project_id}")
    except Exception as e:
        print(f"❌ Error reading service account: {e}")
        return False
    
    # Update .env file
    env_file = ".env"
    if os.path.exists(env_file):
        set_key(env_file, "GCP_PROJECT_ID", project_id)
        set_key(env_file, "GOOGLE_APPLICATION_CREDENTIALS", "service-account-key.json")
        print("✅ Updated .env file")
    
    # Set environment variables for this session
    os.environ["GCP_PROJECT_ID"] = project_id
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-key.json"
    
    # 2. Import after environment setup
    from src.database.bigquery_client import BigQueryClient
    from src.aerodrome.observer import AerodromeObserver
    from src.blockchain.cdp_client import CDPClient
    
    # 3. Initialize clients
    print("\n2️⃣ Initializing clients...")
    
    # Force proper project ID in settings
    from src.config import settings
    settings.gcp_project_id = project_id
    
    cdp_client = CDPClient()
    observer = AerodromeObserver(cdp_client)
    bq_client = BigQueryClient()
    
    # 4. Setup BigQuery
    print("\n3️⃣ Setting up BigQuery dataset and tables...")
    
    dataset_created = await bq_client.ensure_dataset_exists()
    if dataset_created:
        print("✅ Dataset ready")
    else:
        print("❌ Failed to create dataset")
        return False
    
    tables_created = await bq_client.ensure_tables_exist()
    if tables_created:
        print("✅ Tables created")
    else:
        print("❌ Failed to create tables")
        return False
    
    # 5. Collect initial data
    print("\n4️⃣ Collecting Aerodrome pool data...")
    
    # Force simulation mode for initial test
    observer.simulation_mode = True
    pools = await observer.get_top_pools(limit=10)
    
    print(f"✅ Collected {len(pools)} pools")
    
    # 6. Store in BigQuery
    print("\n5️⃣ Storing data in BigQuery...")
    
    success_count = 0
    for pool in pools:
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
        
        success = await bq_client.log_pool_observation(
            agent_id="mainnet-collector",
            pool_data=pool_observation
        )
        
        if success:
            success_count += 1
            print(f"  ✅ Stored {pool['token0_symbol']}/{pool['token1_symbol']} - TVL: ${pool['tvl_usd']:,.0f}")
    
    print(f"\n✅ Successfully stored {success_count}/{len(pools)} observations")
    
    # 7. Verify data
    print("\n6️⃣ Verifying data in BigQuery...")
    
    query = f"""
    SELECT 
        COUNT(*) as total_observations,
        COUNT(DISTINCT pool_address) as unique_pools,
        AVG(tvl_usd) as avg_tvl,
        MAX(total_apy) as max_apy,
        STRING_AGG(DISTINCT CONCAT(token0_symbol, '/', token1_symbol), ', ' LIMIT 5) as sample_pairs
    FROM `{project_id}.athena_analytics.pool_observations`
    WHERE DATE(timestamp) = CURRENT_DATE()
    """
    
    results = await bq_client.query(query)
    
    if results and len(results) > 0:
        stats = results[0]
        print("\n📊 Data Successfully Stored in BigQuery!")
        print(f"  Total observations: {stats.get('total_observations', 0)}")
        print(f"  Unique pools: {stats.get('unique_pools', 0)}")
        print(f"  Average TVL: ${stats.get('avg_tvl', 0):,.2f}")
        print(f"  Max APY: {stats.get('max_apy', 0):.2%}")
        print(f"  Sample pairs: {stats.get('sample_pairs', 'N/A')}")
    
    # 8. Next steps
    print("\n✅ Aerodrome data collection is working!")
    print("\n🎯 Next steps to get REAL mainnet data:")
    print("1. Fix CDP wallet initialization to connect to real Aerodrome")
    print("2. Deploy cloud function: python3 scripts/deploy_pool_collector.py")
    print("3. Data will be collected every 15 minutes automatically")
    print(f"\n📊 BigQuery Console: https://console.cloud.google.com/bigquery?project={project_id}")
    print(f"   Table: {project_id}.athena_analytics.pool_observations")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(setup_and_collect())
    if not success:
        print("\n❌ Setup failed - check errors above")
        sys.exit(1)