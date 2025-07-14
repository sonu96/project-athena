#!/bin/bash

# Project Athena - Secret Manager Setup Script
# This script sets up secrets in GCP Secret Manager

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="project-athena-personal"

echo -e "${GREEN}=== Project Athena Secret Manager Setup ===${NC}"
echo "This script will help you set up secrets in GCP Secret Manager"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Function to create or update a secret
set_secret() {
    local SECRET_NAME=$1
    local SECRET_DESC=$2
    local SECRET_PROMPT=$3
    
    echo -e "\n${YELLOW}Setting up $SECRET_NAME${NC}"
    echo "Description: $SECRET_DESC"
    
    # Check if secret exists
    if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &> /dev/null; then
        echo "Secret $SECRET_NAME already exists"
        read -p "Do you want to update it? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    else
        # Create the secret
        echo "Creating secret $SECRET_NAME..."
        gcloud secrets create $SECRET_NAME \
            --replication-policy="automatic" \
            --project=$PROJECT_ID
    fi
    
    # Get the secret value
    echo "$SECRET_PROMPT"
    read -s SECRET_VALUE
    echo ""
    
    # Add the secret version
    echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME \
        --data-file=- \
        --project=$PROJECT_ID
    
    echo -e "${GREEN}✓ $SECRET_NAME configured${NC}"
}

# Step 1: OpenAI API Key
set_secret "openai-api-key" \
    "OpenAI API key for LLM operations" \
    "Please enter your OpenAI API key:"

# Step 2: Mem0 API Key
set_secret "mem0-api-key" \
    "Mem0 API key for persistent memory" \
    "Please enter your Mem0 API key:"

# Step 3: Agent Private Key
echo -e "\n${YELLOW}Setting up agent-private-key${NC}"
echo "Description: Ethereum private key for the agent's wallet"
echo -e "${RED}WARNING: This is sensitive! Make sure you're using a dedicated wallet${NC}"
read -p "Do you want to set the agent private key? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    set_secret "agent-private-key" \
        "Agent's Ethereum private key" \
        "Please enter the agent's private key (without 0x prefix):"
fi

# Step 4: Grant Cloud Run access to secrets
echo -e "\n${GREEN}Granting Cloud Run access to secrets${NC}"
SERVICE_ACCOUNT="$PROJECT_ID@appspot.gserviceaccount.com"

SECRETS=("openai-api-key" "mem0-api-key" "agent-private-key")
for SECRET in "${SECRETS[@]}"; do
    echo "Granting access to $SECRET..."
    gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID || true
done

# Step 5: List all secrets
echo -e "\n${GREEN}Configured secrets:${NC}"
gcloud secrets list --project=$PROJECT_ID

# Create a template .env.production.local file
echo -e "\n${GREEN}Creating .env.production.local template${NC}"
cat > .env.production.local << EOF
# Production Environment Configuration (LOCAL - DO NOT COMMIT)
# This file contains actual values for local testing

# Core APIs (stored in Secret Manager)
OPENAI_API_KEY=your_actual_openai_key
MEM0_API_KEY=your_actual_mem0_key

# Base Blockchain Configuration
BASE_RPC_URL=https://mainnet.base.org
AGENT_PRIVATE_KEY=your_actual_private_key
AGENT_ADDRESS=your_wallet_address

# GCP Configuration
GCP_PROJECT_ID=$PROJECT_ID
BIGQUERY_DATASET=athena_analytics
FIRESTORE_COLLECTION=agent_memories
GCS_BUCKET_NAME=$PROJECT_ID-storage

# Agent Configuration
INITIAL_TREASURY=1000.0
MODE=PERSONAL

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=INFO
EOF

echo -e "${YELLOW}Created .env.production.local template${NC}"
echo "Update this file with your actual values for local testing"

# Summary
echo -e "\n${GREEN}=== Secret Manager Setup Complete! ===${NC}"
echo ""
echo "Secrets configured in Secret Manager:"
for SECRET in "${SECRETS[@]}"; do
    echo "  ✓ $SECRET"
done
echo ""
echo "Next steps:"
echo "1. Update .env.production.local with your actual values"
echo "2. Ensure GitHub secret GCP_SA_KEY is set"
echo "3. Deploy your application"
echo ""
echo -e "${GREEN}Your secrets are securely stored! 🔐${NC}"