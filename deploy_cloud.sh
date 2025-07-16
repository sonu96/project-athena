#!/bin/bash

# Athena Agent - Cloud Deployment Script

set -e

# Configuration
PROJECT_ID="project-athena-development"
REGION="us-central1"
SERVICE_NAME="athena-agent-mainnet"
IMAGE_NAME="gcr.io/${PROJECT_ID}/athena-agent:latest"

echo "🚀 Deploying Athena Agent to Google Cloud Run"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Build Docker image
echo "Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Push to Google Container Registry
echo "Pushing image to GCR..."
docker push ${IMAGE_NAME}

# Create service account if it doesn't exist
echo "Setting up service account..."
gcloud iam service-accounts create athena-agent-sa \
    --display-name="Athena Agent Service Account" \
    2>/dev/null || echo "Service account already exists"

# Grant necessary permissions
echo "Setting IAM permissions..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:athena-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:athena-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:athena-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --region ${REGION} \
    --platform managed \
    --service-account athena-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars "ENVIRONMENT=production" \
    --set-env-vars "NETWORK=base" \
    --set-env-vars "OBSERVATION_MODE=true" \
    --set-secrets "CDP_API_KEY_NAME=cdp-api-key-name:latest" \
    --set-secrets "CDP_API_KEY_SECRET=cdp-api-key-secret:latest" \
    --set-secrets "MEM0_API_KEY=mem0-api-key:latest" \
    --set-secrets "LANGSMITH_API_KEY=langsmith-api-key:latest" \
    --memory 4Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 3 \
    --min-instances 1 \
    --allow-unauthenticated

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📊 View logs:"
echo "gcloud logging read \"resource.labels.service_name=${SERVICE_NAME}\" --limit=50"
echo ""
echo "📈 Monitor metrics:"
echo "https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics"