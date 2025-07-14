#!/bin/bash

# Project Athena - GCP Setup Script
# This script sets up the GCP project and required services

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="project-athena-personal"
REGION="us-central1"
SERVICE_ACCOUNT_NAME="athena-deployer"

echo -e "${GREEN}=== Project Athena GCP Setup ===${NC}"
echo "This script will set up your GCP project for Project Athena deployment"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}Please log in to Google Cloud${NC}"
    gcloud auth login
fi

# Step 1: Create or select project
echo -e "\n${GREEN}Step 1: Setting up GCP Project${NC}"
if gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo "Project $PROJECT_ID already exists"
else
    echo "Creating new project: $PROJECT_ID"
    gcloud projects create $PROJECT_ID --name="Project Athena Personal"
fi

# Set the project as default
gcloud config set project $PROJECT_ID

# Step 2: Enable billing (manual step)
echo -e "\n${YELLOW}Step 2: Enable Billing${NC}"
echo "Please ensure billing is enabled for project $PROJECT_ID"
echo "Visit: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
read -p "Press Enter when billing is enabled..."

# Step 3: Enable required APIs
echo -e "\n${GREEN}Step 3: Enabling Required APIs${NC}"
APIS=(
    "run.googleapis.com"              # Cloud Run
    "cloudbuild.googleapis.com"       # Cloud Build
    "secretmanager.googleapis.com"    # Secret Manager
    "firestore.googleapis.com"        # Firestore
    "storage.googleapis.com"          # Cloud Storage
    "containerregistry.googleapis.com" # Container Registry
    "logging.googleapis.com"          # Cloud Logging
    "monitoring.googleapis.com"       # Cloud Monitoring
)

for API in "${APIS[@]}"; do
    echo "Enabling $API..."
    gcloud services enable $API --project=$PROJECT_ID
done

# Step 4: Create service account
echo -e "\n${GREEN}Step 4: Creating Service Account${NC}"
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" &> /dev/null; then
    echo "Service account already exists"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Athena Deployer" \
        --project=$PROJECT_ID
fi

# Step 5: Grant necessary permissions
echo -e "\n${GREEN}Step 5: Granting Permissions${NC}"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

ROLES=(
    "roles/run.admin"
    "roles/storage.admin"
    "roles/cloudbuild.builds.builder"
    "roles/secretmanager.admin"
    "roles/firestore.user"
    "roles/logging.admin"
    "roles/monitoring.metricWriter"
)

for ROLE in "${ROLES[@]}"; do
    echo "Granting $ROLE..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$ROLE" \
        --project=$PROJECT_ID
done

# Step 6: Create and download service account key
echo -e "\n${GREEN}Step 6: Creating Service Account Key${NC}"
KEY_FILE="./gcp-service-account-key.json"
if [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}Service account key already exists at $KEY_FILE${NC}"
else
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SERVICE_ACCOUNT_EMAIL \
        --project=$PROJECT_ID
    echo -e "${GREEN}Service account key saved to: $KEY_FILE${NC}"
fi

# Step 7: Create Firestore database
echo -e "\n${GREEN}Step 7: Creating Firestore Database${NC}"
if gcloud firestore databases describe --project=$PROJECT_ID &> /dev/null; then
    echo "Firestore database already exists"
else
    echo "Creating Firestore database in $REGION..."
    gcloud firestore databases create \
        --region=$REGION \
        --project=$PROJECT_ID
fi

# Step 8: Create Cloud Storage bucket
echo -e "\n${GREEN}Step 8: Creating Cloud Storage Bucket${NC}"
BUCKET_NAME="$PROJECT_ID-storage"
if gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
    echo "Bucket gs://$BUCKET_NAME already exists"
else
    echo "Creating bucket gs://$BUCKET_NAME..."
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME/
fi

# Step 9: Create secrets in Secret Manager
echo -e "\n${GREEN}Step 9: Setting up Secret Manager${NC}"
echo -e "${YELLOW}You'll need to manually add your API keys to Secret Manager${NC}"
echo "Run these commands with your actual keys:"
echo ""
echo "  echo -n 'YOUR_OPENAI_KEY' | gcloud secrets create openai-api-key --data-file=- --project=$PROJECT_ID"
echo "  echo -n 'YOUR_MEM0_KEY' | gcloud secrets create mem0-api-key --data-file=- --project=$PROJECT_ID"
echo "  echo -n 'YOUR_PRIVATE_KEY' | gcloud secrets create agent-private-key --data-file=- --project=$PROJECT_ID"
echo ""

# Step 10: Set up budget alert
echo -e "\n${GREEN}Step 10: Budget Alert Setup${NC}"
echo -e "${YELLOW}Set up budget alerts in the Console to stay under $50/month${NC}"
echo "Visit: https://console.cloud.google.com/billing/budgets?project=$PROJECT_ID"
echo ""

# Summary
echo -e "\n${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Add the service account key to GitHub Secrets:"
echo "   - Name: GCP_SA_KEY"
echo "   - Value: Contents of $KEY_FILE"
echo ""
echo "2. Add your API keys to Secret Manager (see commands above)"
echo ""
echo "3. Update .env.production with:"
echo "   - GCP_PROJECT_ID=$PROJECT_ID"
echo "   - Other configuration values"
echo ""
echo "4. Push to main branch to trigger deployment"
echo ""
echo -e "${YELLOW}Important files created:${NC}"
echo "  - Service Account Key: $KEY_FILE"
echo "  - Project ID: $PROJECT_ID"
echo "  - Bucket: gs://$BUCKET_NAME"
echo ""
echo -e "${GREEN}Happy deploying! 🚀${NC}"