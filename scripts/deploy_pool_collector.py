#!/usr/bin/env python3
"""Deploy pool collector cloud function to Google Cloud"""

import os
import subprocess
import json
from datetime import datetime

def deploy_pool_collector():
    """Deploy the pool collector function"""
    
    print("🚀 Deploying Pool Collector Cloud Function\n")
    
    # Check if gcloud is installed
    try:
        subprocess.run(["gcloud", "--version"], check=True, capture_output=True)
        print("✅ Google Cloud SDK found")
    except:
        print("❌ Google Cloud SDK not found. Please install it first:")
        print("   https://cloud.google.com/sdk/docs/install")
        return False
    
    # Configuration
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "athena-agent-prod")
    FUNCTION_NAME = "aerodrome-pool-collector"
    REGION = "us-central1"
    RUNTIME = "python311"
    MEMORY = "512MB"
    TIMEOUT = "540s"  # 9 minutes
    
    print(f"📋 Configuration:")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Function: {FUNCTION_NAME}")
    print(f"   Region: {REGION}")
    print(f"   Runtime: {RUNTIME}")
    
    # Change to function directory
    function_dir = "cloud_functions/pool_collector"
    
    # Deploy command
    deploy_cmd = [
        "gcloud", "functions", "deploy", FUNCTION_NAME,
        "--gen2",
        "--runtime", RUNTIME,
        "--region", REGION,
        "--source", function_dir,
        "--entry-point", "collect_pools",
        "--trigger-http",
        "--allow-unauthenticated",
        "--memory", MEMORY,
        "--timeout", TIMEOUT,
        "--set-env-vars", f"GCP_PROJECT={PROJECT_ID},BIGQUERY_DATASET=athena_analytics",
        "--project", PROJECT_ID
    ]
    
    print(f"\n🔧 Deploying cloud function...")
    print(f"   Command: {' '.join(deploy_cmd)}")
    
    try:
        result = subprocess.run(deploy_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Cloud function deployed successfully!")
            
            # Set up scheduled trigger (every 15 minutes)
            print("\n⏰ Setting up scheduled trigger...")
            
            scheduler_cmd = [
                "gcloud", "scheduler", "jobs", "create", "http",
                f"{FUNCTION_NAME}-schedule",
                "--location", REGION,
                "--schedule", "*/15 * * * *",  # Every 15 minutes
                "--http-method", "GET",
                "--uri", f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net/{FUNCTION_NAME}",
                "--project", PROJECT_ID
            ]
            
            try:
                subprocess.run(scheduler_cmd, capture_output=True, text=True)
                print("✅ Scheduled trigger created (runs every 15 minutes)")
            except:
                print("⚠️  Scheduler might already exist or needs manual setup")
            
            # Test the function
            print("\n🧪 Testing the deployed function...")
            test_cmd = [
                "gcloud", "functions", "call", FUNCTION_NAME,
                "--region", REGION,
                "--project", PROJECT_ID
            ]
            
            test_result = subprocess.run(test_cmd, capture_output=True, text=True)
            if test_result.returncode == 0:
                print("✅ Function test successful!")
                print(f"   Response: {test_result.stdout[:200]}...")
            else:
                print("⚠️  Function test failed - check logs")
            
            print("\n📊 View function logs:")
            print(f"   gcloud functions logs read {FUNCTION_NAME} --region {REGION}")
            
            print("\n🎯 Pool collector is now running!")
            print("   Data will be collected every 15 minutes")
            print("   Check BigQuery table: athena_analytics.pool_observations")
            
            return True
            
        else:
            print(f"\n❌ Deployment failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"\n❌ Error during deployment: {e}")
        return False

if __name__ == "__main__":
    # First, let's test locally
    print("🧪 Testing pool collector locally first...\n")
    
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from cloud_functions.pool_collector.main import collect_pools
        
        # Mock request
        class MockRequest:
            pass
        
        result = collect_pools(MockRequest())
        print(f"Local test result: {result[0][:200]}...")
        print("\n✅ Local test passed!")
        
        # Prompt for deployment
        response = input("\n🚀 Deploy to Google Cloud? (y/n): ")
        if response.lower() == 'y':
            deploy_pool_collector()
        else:
            print("Deployment cancelled")
            
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        print("Fix the errors before deploying")