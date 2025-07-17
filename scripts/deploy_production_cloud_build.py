#!/usr/bin/env python3
"""Deploy Athena Agent Phase 1 using Cloud Build (no local Docker required)"""

import os
import subprocess
import json
import sys
from datetime import datetime

# Configuration
PROJECT_ID = "athena-defi-agent-1752635199"
REGION = "us-central1"
SERVICE_NAME = "athena-agent-phase1"

def run_command(cmd, description):
    """Run a command and handle output"""
    print(f"\n🔧 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"   ✅ Success")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e.stderr}")
        return None

def deploy_phase1_cloud_build():
    """Deploy Phase 1 using Cloud Build"""
    
    print("🚀 Athena Agent Phase 1 Production Deployment (Cloud Build)\n")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Region: {REGION}")
    print(f"   Service: {SERVICE_NAME}")
    
    # Step 1: Set project and enable APIs
    print("\n1️⃣ Configuring Google Cloud...")
    
    run_command(
        ["gcloud", "config", "set", "project", PROJECT_ID],
        "Setting project"
    )
    
    apis = [
        "cloudbuild.googleapis.com",
        "run.googleapis.com",
        "artifactregistry.googleapis.com",
        "cloudscheduler.googleapis.com",
        "cloudfunctions.googleapis.com"
    ]
    
    for api in apis:
        run_command(
            ["gcloud", "services", "enable", api],
            f"Enabling {api}"
        )
    
    # Step 2: Submit build to Cloud Build
    print("\n2️⃣ Building container with Cloud Build...")
    
    build_result = run_command(
        [
            "gcloud", "builds", "submit",
            "--tag", f"gcr.io/{PROJECT_ID}/athena-agent:phase1",
            "."
        ],
        "Submitting build to Cloud Build"
    )
    
    if not build_result:
        print("❌ Cloud Build failed")
        return False
    
    # Step 3: Deploy pool collector cloud function
    print("\n3️⃣ Deploying pool collector cloud function...")
    
    deploy_result = run_command(
        [
            "gcloud", "functions", "deploy", "aerodrome-pool-collector",
            "--gen2",
            "--runtime", "python311",
            "--region", REGION,
            "--source", "cloud_functions/pool_collector",
            "--entry-point", "collect_pools",
            "--trigger-http",
            "--allow-unauthenticated",
            "--memory", "512MB",
            "--timeout", "540s",
            "--set-env-vars", f"GCP_PROJECT={PROJECT_ID},BIGQUERY_DATASET=athena_analytics"
        ],
        "Deploying pool collector function"
    )
    
    if deploy_result:
        # Set up scheduler
        run_command(
            [
                "gcloud", "scheduler", "jobs", "create", "http",
                "aerodrome-pool-collector-schedule",
                "--location", REGION,
                "--schedule", "*/15 * * * *",
                "--http-method", "GET",
                "--uri", f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net/aerodrome-pool-collector"
            ],
            "Creating scheduled trigger (every 15 minutes)"
        )
    
    # Step 4: Create service account
    print("\n4️⃣ Setting up service account...")
    
    sa_email = f"athena-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com"
    
    run_command(
        ["gcloud", "iam", "service-accounts", "create", "athena-agent-sa", 
         "--display-name", "Athena Agent Service Account"],
        "Creating service account"
    )
    
    # Grant permissions
    roles = [
        "roles/bigquery.dataEditor",
        "roles/datastore.user",
        "roles/secretmanager.secretAccessor",
        "roles/logging.logWriter"
    ]
    
    for role in roles:
        run_command(
            [
                "gcloud", "projects", "add-iam-policy-binding", PROJECT_ID,
                "--member", f"serviceAccount:{sa_email}",
                "--role", role
            ],
            f"Granting {role}"
        )
    
    # Step 5: Deploy to Cloud Run
    print("\n5️⃣ Deploying main agent to Cloud Run...")
    
    # Read environment variables from .env
    env_vars = []
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key = line.split("=")[0]
                    if key in ["MEM0_API_KEY", "LANGSMITH_API_KEY", "CDP_API_KEY_NAME", "CDP_API_KEY_SECRET"]:
                        env_vars.append(line)
    
    # Add production settings
    env_vars.extend([
        f"GCP_PROJECT_ID={PROJECT_ID}",
        "BIGQUERY_DATASET=athena_analytics",
        "OBSERVATION_MODE=true",
        "NETWORK=base",
        "ENV=production",
        "LOG_LEVEL=INFO",
        "AGENT_ID=athena-phase1-prod"
    ])
    
    deploy_cmd = [
        "gcloud", "run", "deploy", SERVICE_NAME,
        "--image", f"gcr.io/{PROJECT_ID}/athena-agent:phase1",
        "--region", REGION,
        "--platform", "managed",
        "--service-account", sa_email,
        "--memory", "2Gi",
        "--cpu", "1",
        "--timeout", "3600",
        "--max-instances", "3",
        "--min-instances", "1",
        "--port", "8080",
        "--allow-unauthenticated",
        "--set-env-vars", ",".join(env_vars)
    ]
    
    deploy_result = run_command(deploy_cmd, "Deploying to Cloud Run")
    
    if not deploy_result:
        print("❌ Cloud Run deployment failed")
        return False
    
    # Get service URL
    url_result = run_command(
        ["gcloud", "run", "services", "describe", SERVICE_NAME, "--region", REGION, 
         "--format", "value(status.url)"],
        "Getting service URL"
    )
    
    if url_result:
        service_url = url_result.strip()
        print(f"\n✅ Service deployed at: {service_url}")
        
        # Test the deployment
        print("\n6️⃣ Testing deployment...")
        
        import time
        time.sleep(10)  # Wait for service to start
        
        try:
            import requests
            response = requests.get(f"{service_url}/health", timeout=30)
            if response.status_code == 200:
                print("   ✅ Health check passed!")
                print(f"   Response: {response.json()}")
            else:
                print(f"   ⚠️  Health check returned {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Health check failed: {e}")
    
    print("\n" + "="*60)
    print("✅ PHASE 1 PRODUCTION DEPLOYMENT COMPLETE!")
    print("="*60)
    
    print(f"\n📊 Deployment Summary:")
    print(f"   - Container Image: gcr.io/{PROJECT_ID}/athena-agent:phase1")
    print(f"   - Cloud Run Service: {SERVICE_NAME}")
    print(f"   - Pool Collector: Running every 15 minutes")
    print(f"   - Service URL: {service_url if 'service_url' in locals() else 'Check Cloud Console'}")
    
    print(f"\n🔗 View in Console:")
    print(f"   - Cloud Run: https://console.cloud.google.com/run/detail/{REGION}/{SERVICE_NAME}?project={PROJECT_ID}")
    print(f"   - Logs: https://console.cloud.google.com/logs?project={PROJECT_ID}")
    print(f"   - BigQuery: https://console.cloud.google.com/bigquery?project={PROJECT_ID}")
    
    # Check initial logs
    print(f"\n📝 Recent logs:")
    run_command(
        ["gcloud", "run", "logs", "read", SERVICE_NAME, "--region", REGION, "--limit", "10"],
        "Fetching initial logs"
    )
    
    return True

if __name__ == "__main__":
    print("⚠️  This will deploy Athena Agent Phase 1 to production using Cloud Build.")
    print(f"   Project: {PROJECT_ID}")
    print("   No local Docker required!")
    
    response = input("\nProceed with deployment? (yes/no): ")
    
    if response.lower() == "yes":
        success = deploy_phase1_cloud_build()
        if not success:
            print("\n❌ Deployment failed. Check errors above.")
            sys.exit(1)
        else:
            print("\n🎉 Deployment successful! Your agent is now running 24/7!")
    else:
        print("Deployment cancelled.")