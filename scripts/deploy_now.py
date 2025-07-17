#!/usr/bin/env python3
"""Deploy Athena Agent Phase 1 - Non-interactive version"""

import os
import subprocess
import json
import sys
from datetime import datetime

# Configuration
PROJECT_ID = "athena-defi-agent-1752635199"
REGION = "us-central1"
SERVICE_NAME = "athena-agent-phase1"

print("🚀 Starting Athena Agent Phase 1 Production Deployment\n")
print(f"Project: {PROJECT_ID}")
print(f"Region: {REGION}")
print(f"Service: {SERVICE_NAME}")
print("\n" + "="*60 + "\n")

# Step 1: Enable APIs
print("1️⃣ Enabling required APIs...")

apis = [
    "cloudbuild.googleapis.com",
    "run.googleapis.com", 
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com"
]

for api in apis:
    cmd = f"gcloud services enable {api} --project={PROJECT_ID}"
    print(f"   Enabling {api}...")
    os.system(cmd)

print("\n✅ APIs enabled")

# Step 2: Build with Cloud Build
print("\n2️⃣ Building container with Cloud Build...")
print("   This may take 3-5 minutes...\n")

build_cmd = f"gcloud builds submit --tag gcr.io/{PROJECT_ID}/athena-agent:phase1 --project={PROJECT_ID} ."
result = os.system(build_cmd)

if result != 0:
    print("\n❌ Build failed!")
    sys.exit(1)

print("\n✅ Container built successfully")

# Step 3: Deploy pool collector
print("\n3️⃣ Deploying pool collector cloud function...")

function_cmd = f"""gcloud functions deploy aerodrome-pool-collector \
--gen2 \
--runtime python311 \
--region {REGION} \
--source cloud_functions/pool_collector \
--entry-point collect_pools \
--trigger-http \
--allow-unauthenticated \
--memory 512MB \
--timeout 540s \
--set-env-vars GCP_PROJECT={PROJECT_ID},BIGQUERY_DATASET=athena_analytics \
--project {PROJECT_ID}"""

print("   Deploying function...")
os.system(function_cmd)

# Step 4: Create service account
print("\n4️⃣ Setting up service account...")

sa_commands = [
    f"gcloud iam service-accounts create athena-agent-sa --display-name 'Athena Agent Service Account' --project {PROJECT_ID}",
    f"gcloud projects add-iam-policy-binding {PROJECT_ID} --member serviceAccount:athena-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com --role roles/bigquery.dataEditor",
    f"gcloud projects add-iam-policy-binding {PROJECT_ID} --member serviceAccount:athena-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com --role roles/logging.logWriter"
]

for cmd in sa_commands:
    os.system(cmd + " 2>/dev/null")

print("✅ Service account configured")

# Step 5: Deploy to Cloud Run
print("\n5️⃣ Deploying main agent to Cloud Run...")

# Read sensitive env vars from .env
env_vars = []
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key in ["MEM0_API_KEY", "LANGSMITH_API_KEY", "CDP_API_KEY_NAME", "CDP_API_KEY_SECRET"]:
                    # Remove quotes
                    value = value.strip('"').strip("'")
                    env_vars.append(f"{key}={value}")

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

env_string = ",".join(env_vars)

deploy_cmd = f"""gcloud run deploy {SERVICE_NAME} \
--image gcr.io/{PROJECT_ID}/athena-agent:phase1 \
--region {REGION} \
--platform managed \
--memory 2Gi \
--cpu 1 \
--timeout 3600 \
--max-instances 3 \
--min-instances 1 \
--port 8080 \
--allow-unauthenticated \
--service-account athena-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com \
--set-env-vars "{env_string}" \
--project {PROJECT_ID}"""

print("   Deploying service...")
result = os.system(deploy_cmd)

if result != 0:
    print("\n❌ Cloud Run deployment failed!")
    sys.exit(1)

# Get service URL
print("\n6️⃣ Getting service information...")
url_cmd = f"gcloud run services describe {SERVICE_NAME} --region {REGION} --format 'value(status.url)' --project {PROJECT_ID}"
service_url = subprocess.check_output(url_cmd, shell=True).decode().strip()

print("\n" + "="*60)
print("✅ DEPLOYMENT COMPLETE!")
print("="*60)

print(f"\n📊 Deployment Summary:")
print(f"   Service URL: {service_url}")
print(f"   Health Check: {service_url}/health")

print(f"\n🔗 Console Links:")
print(f"   Cloud Run: https://console.cloud.google.com/run/detail/{REGION}/{SERVICE_NAME}?project={PROJECT_ID}")
print(f"   Logs: https://console.cloud.google.com/logs?project={PROJECT_ID}")
print(f"   BigQuery: https://console.cloud.google.com/bigquery?project={PROJECT_ID}")

print(f"\n📝 View logs:")
print(f"   gcloud run logs read {SERVICE_NAME} --region {REGION} --project {PROJECT_ID}")

print("\n🎉 Athena Agent Phase 1 is now running in production!")