#!/usr/bin/env python3
"""Deploy Athena Agent Phase 1 to Production"""

import os
import subprocess
import json
import sys
from datetime import datetime

# Configuration
PROJECT_ID = "athena-defi-agent-1752635199"  # Using current active project
REGION = "us-central1"
SERVICE_NAME = "athena-agent-phase1"
IMAGE_NAME = f"gcr.io/{PROJECT_ID}/athena-agent"

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

def deploy_phase1():
    """Deploy Phase 1 Production"""
    
    print("🚀 Athena Agent Phase 1 Production Deployment\n")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Region: {REGION}")
    print(f"   Service: {SERVICE_NAME}")
    
    # Step 1: Verify gcloud configuration
    print("\n1️⃣ Verifying Google Cloud configuration...")
    
    # Set project
    run_command(
        ["gcloud", "config", "set", "project", PROJECT_ID],
        "Setting project"
    )
    
    # Enable required APIs
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
    
    # Step 2: Build Docker image
    print("\n2️⃣ Building Docker container...")
    
    # Configure docker for gcr.io
    run_command(
        ["gcloud", "auth", "configure-docker"],
        "Configuring Docker authentication"
    )
    
    # Build image
    build_result = run_command(
        ["docker", "build", "-t", f"{IMAGE_NAME}:latest", "-t", f"{IMAGE_NAME}:phase1", "."],
        "Building Docker image"
    )
    
    if not build_result:
        print("❌ Docker build failed. Make sure Docker is running.")
        return False
    
    # Step 3: Push to Container Registry
    print("\n3️⃣ Pushing to Google Container Registry...")
    
    push_result = run_command(
        ["docker", "push", f"{IMAGE_NAME}:latest"],
        "Pushing latest tag"
    )
    
    if not push_result:
        print("❌ Docker push failed.")
        return False
    
    run_command(
        ["docker", "push", f"{IMAGE_NAME}:phase1"],
        "Pushing phase1 tag"
    )
    
    # Step 4: Deploy pool collector cloud function
    print("\n4️⃣ Deploying pool collector cloud function...")
    
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
    
    # Step 5: Deploy main agent to Cloud Run
    print("\n5️⃣ Deploying main agent to Cloud Run...")
    
    # Create service account if needed
    sa_email = f"athena-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com"
    run_command(
        ["gcloud", "iam", "service-accounts", "create", "athena-agent-sa", "--display-name", "Athena Agent Service Account"],
        "Creating service account"
    )
    
    # Grant necessary permissions
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
    
    # Deploy to Cloud Run
    print("\n   Deploying Cloud Run service...")
    
    deploy_cmd = [
        "gcloud", "run", "deploy", SERVICE_NAME,
        "--image", f"{IMAGE_NAME}:phase1",
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
        "--set-env-vars", ",".join([
            f"GCP_PROJECT_ID={PROJECT_ID}",
            "BIGQUERY_DATASET=athena_analytics",
            "OBSERVATION_MODE=true",
            "NETWORK=base",
            "ENV=production",
            "LOG_LEVEL=INFO"
        ])
    ]
    
    deploy_result = run_command(deploy_cmd, "Deploying to Cloud Run")
    
    if not deploy_result:
        print("❌ Cloud Run deployment failed")
        return False
    
    # Get service URL
    url_result = run_command(
        ["gcloud", "run", "services", "describe", SERVICE_NAME, "--region", REGION, "--format", "value(status.url)"],
        "Getting service URL"
    )
    
    if url_result:
        service_url = url_result.strip()
        print(f"\n✅ Service deployed at: {service_url}")
        
        # Test the deployment
        print("\n6️⃣ Testing deployment...")
        
        import requests
        try:
            response = requests.get(f"{service_url}/health", timeout=10)
            if response.status_code == 200:
                print("   ✅ Health check passed!")
                print(f"   Response: {response.json()}")
            else:
                print(f"   ⚠️  Health check returned {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Health check failed: {e}")
    
    # Step 6: Set up monitoring
    print("\n7️⃣ Setting up monitoring...")
    
    # Create uptime check
    run_command(
        [
            "gcloud", "monitoring", "uptime-checks", "create",
            f"{SERVICE_NAME}-health",
            "--display-name", "Athena Agent Health Check",
            "--resource-type", "cloud-run-revision",
            "--service", SERVICE_NAME,
            "--location", REGION,
            "--check-interval", "5m"
        ],
        "Creating uptime monitoring"
    )
    
    print("\n" + "="*60)
    print("✅ PHASE 1 PRODUCTION DEPLOYMENT COMPLETE!")
    print("="*60)
    
    print(f"\n📊 Deployment Summary:")
    print(f"   - Docker Image: {IMAGE_NAME}:phase1")
    print(f"   - Cloud Run Service: {SERVICE_NAME}")
    print(f"   - Pool Collector: Running every 15 minutes")
    print(f"   - BigQuery Dataset: athena_analytics")
    print(f"   - Service URL: {service_url if 'service_url' in locals() else 'Check Cloud Console'}")
    
    print(f"\n🔗 Useful Links:")
    print(f"   - Cloud Run: https://console.cloud.google.com/run/detail/{REGION}/{SERVICE_NAME}?project={PROJECT_ID}")
    print(f"   - Logs: https://console.cloud.google.com/logs?project={PROJECT_ID}&query=resource.labels.service_name%3D%22{SERVICE_NAME}%22")
    print(f"   - BigQuery: https://console.cloud.google.com/bigquery?project={PROJECT_ID}")
    
    print(f"\n🎯 Next Steps:")
    print("   1. Monitor logs for the first few cycles")
    print("   2. Verify pool data is being collected in BigQuery")
    print("   3. Check cost tracking and alerts")
    print("   4. Set up Grafana dashboard for visualization")
    
    return True

if __name__ == "__main__":
    # Confirm deployment
    print("⚠️  This will deploy Athena Agent Phase 1 to production.")
    print(f"   Project: {PROJECT_ID}")
    response = input("\nProceed with deployment? (yes/no): ")
    
    if response.lower() == "yes":
        success = deploy_phase1()
        if not success:
            print("\n❌ Deployment failed. Check errors above.")
            sys.exit(1)
    else:
        print("Deployment cancelled.")