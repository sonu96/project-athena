#!/bin/bash

# Athena Agent - Google Cloud Setup Script

set -e  # Exit on error

echo "🏛️ Athena Agent - Google Cloud Setup"
echo "===================================="
echo

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current account
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
echo "Current Google account: $CURRENT_ACCOUNT"
echo

# Set project variables
PROJECT_ID="athena-defi-agent-$(date +%s)"
PROJECT_NAME="Athena DeFi Agent"
BILLING_ACCOUNT=""

echo "📋 Project Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Project Name: $PROJECT_NAME"
echo

# Confirm creation
read -p "Create new project? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Create project
echo "1️⃣ Creating project..."
gcloud projects create $PROJECT_ID \
    --name="$PROJECT_NAME" \
    --set-as-default

echo "✅ Project created: $PROJECT_ID"

# Set as default
gcloud config set project $PROJECT_ID

# Link billing account (optional)
echo
echo "2️⃣ Billing Account Setup"
echo "Available billing accounts:"
gcloud billing accounts list

read -p "Enter billing account ID (or press Enter to skip): " BILLING_ACCOUNT
if [ ! -z "$BILLING_ACCOUNT" ]; then
    gcloud billing projects link $PROJECT_ID \
        --billing-account=$BILLING_ACCOUNT
    echo "✅ Billing account linked"
else
    echo "⚠️  No billing account linked (some services may be limited)"
fi

# Enable required APIs
echo
echo "3️⃣ Enabling required APIs..."

APIS=(
    "firestore.googleapis.com"
    "bigquery.googleapis.com"
    "secretmanager.googleapis.com"
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "monitoring.googleapis.com"
    "logging.googleapis.com"
)

for API in "${APIS[@]}"; do
    echo "   Enabling $API..."
    gcloud services enable $API --project=$PROJECT_ID
done

echo "✅ APIs enabled"

# Create Firestore database
echo
echo "4️⃣ Creating Firestore database..."
gcloud firestore databases create \
    --location=us-central1 \
    --project=$PROJECT_ID \
    --quiet || echo "Firestore may already exist"

# Create BigQuery dataset
echo
echo "5️⃣ Creating BigQuery dataset..."
bq mk --dataset \
    --location=US \
    --project_id=$PROJECT_ID \
    athena_analytics || echo "Dataset may already exist"

# Create service account
echo
echo "6️⃣ Creating service account..."
SERVICE_ACCOUNT_NAME="athena-agent-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Athena Agent Service Account" \
    --project=$PROJECT_ID

# Grant permissions
echo "   Granting permissions..."
ROLES=(
    "roles/firestore.user"
    "roles/bigquery.dataEditor"
    "roles/bigquery.jobUser"
    "roles/secretmanager.secretAccessor"
    "roles/logging.logWriter"
    "roles/monitoring.metricWriter"
)

for ROLE in "${ROLES[@]}"; do
    echo "   Adding role: $ROLE"
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="$ROLE" \
        --quiet
done

# Create and download key
echo
echo "7️⃣ Creating service account key..."
KEY_PATH="./credentials/gcp-service-account.json"
mkdir -p credentials

gcloud iam service-accounts keys create $KEY_PATH \
    --iam-account=$SERVICE_ACCOUNT_EMAIL \
    --project=$PROJECT_ID

echo "✅ Service account key saved to: $KEY_PATH"

# Create .env entries
echo
echo "8️⃣ Generating .env configuration..."
cat << EOF > .env.gcp

# Google Cloud Platform Configuration
GCP_PROJECT_ID="$PROJECT_ID"
GOOGLE_APPLICATION_CREDENTIALS="$KEY_PATH"
FIRESTORE_DATABASE="(default)"
BIGQUERY_DATASET="athena_analytics"
EOF

echo "✅ GCP configuration saved to .env.gcp"

# Summary
echo
echo "========================================="
echo "✅ Google Cloud setup complete!"
echo "========================================="
echo
echo "Project ID: $PROJECT_ID"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "Credentials: $KEY_PATH"
echo
echo "Next steps:"
echo "1. Add the contents of .env.gcp to your .env file"
echo "2. Run: python scripts/configure.py --test"
echo
echo "To delete this project later:"
echo "  gcloud projects delete $PROJECT_ID"
echo