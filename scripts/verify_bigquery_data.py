#!/usr/bin/env python3
"""Verify Aerodrome data in BigQuery"""

import os
import json
from google.cloud import bigquery
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def verify_bigquery_data():
    """Check if data is flowing to BigQuery"""
    
    print("🔍 Verifying BigQuery Data\n")
    
    # Get project ID
    with open("service-account-key.json", "r") as f:
        project_id = json.load(f)["project_id"]
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-key.json"
    
    # Initialize BigQuery client
    client = bigquery.Client(project=project_id)
    
    # Check if dataset exists
    dataset_id = "athena_analytics"
    dataset_ref = client.dataset(dataset_id)
    
    try:
        dataset = client.get_dataset(dataset_ref)
        print(f"✅ Dataset '{dataset_id}' exists")
        print(f"   Location: {dataset.location}")
        print(f"   Created: {dataset.created}")
    except Exception as e:
        print(f"❌ Dataset not found: {e}")
        return
    
    # List tables
    print(f"\n📋 Tables in {dataset_id}:")
    tables = list(client.list_tables(dataset_ref))
    
    if not tables:
        print("   No tables found")
        return
    
    for table in tables:
        print(f"   - {table.table_id}")
        
        # Get table info
        table_ref = dataset_ref.table(table.table_id)
        table_obj = client.get_table(table_ref)
        print(f"     Rows: {table_obj.num_rows:,}")
        print(f"     Size: {table_obj.num_bytes / 1024 / 1024:.2f} MB")
    
    # Query pool_observations
    print("\n📊 Pool Observations Data:")
    
    query = f"""
    SELECT 
        timestamp,
        pool_address,
        CONCAT(token0_symbol, '/', token1_symbol) as pair,
        pool_type,
        tvl_usd,
        volume_24h_usd,
        total_apy
    FROM `{project_id}.{dataset_id}.pool_observations`
    ORDER BY timestamp DESC
    LIMIT 10
    """
    
    try:
        results = client.query(query).result()
        
        print("\nLatest Pool Observations:")
        print("-" * 100)
        print(f"{'Timestamp':<25} {'Pair':<15} {'Type':<10} {'TVL':<15} {'Volume 24h':<15} {'APY':<10}")
        print("-" * 100)
        
        for row in results:
            timestamp = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            print(f"{timestamp:<25} {row['pair']:<15} {row['pool_type']:<10} "
                  f"${row['tvl_usd']:>13,.0f} ${row['volume_24h_usd']:>13,.0f} "
                  f"{row['total_apy']:>8.2%}")
        
        # Get summary statistics
        summary_query = f"""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT pool_address) as unique_pools,
            COUNT(DISTINCT DATE(timestamp)) as days_with_data,
            MIN(timestamp) as first_record,
            MAX(timestamp) as last_record,
            AVG(tvl_usd) as avg_tvl,
            SUM(tvl_usd) as total_tvl
        FROM `{project_id}.{dataset_id}.pool_observations`
        """
        
        summary = client.query(summary_query).result()
        stats = list(summary)[0]
        
        print("\n📈 Summary Statistics:")
        print(f"   Total records: {stats['total_records']:,}")
        print(f"   Unique pools: {stats['unique_pools']}")
        print(f"   Days with data: {stats['days_with_data']}")
        print(f"   First record: {stats['first_record']}")
        print(f"   Last record: {stats['last_record']}")
        print(f"   Average TVL: ${stats['avg_tvl']:,.2f}")
        print(f"   Total TVL tracked: ${stats['total_tvl']:,.2f}")
        
        print("\n✅ Data is successfully flowing to BigQuery!")
        print(f"\n🔗 View in BigQuery Console:")
        print(f"   https://console.cloud.google.com/bigquery?project={project_id}&ws=!1m5!1m4!4m3!1s{project_id}!2s{dataset_id}!3spool_observations")
        
    except Exception as e:
        print(f"❌ Error querying data: {e}")
        print("\n💡 This might be normal if the table was just created.")
        print("   BigQuery needs a few seconds to propagate. Try again in a moment.")

if __name__ == "__main__":
    verify_bigquery_data()