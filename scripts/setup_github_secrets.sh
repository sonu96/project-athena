#!/bin/bash

# Project Athena - GitHub Secrets Setup Script
# This script helps set up GitHub secrets for deployment

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Project Athena GitHub Secrets Setup ===${NC}"
echo "This script will help you set up GitHub secrets for CI/CD"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Please install GitHub CLI: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}Please log in to GitHub${NC}"
    gh auth login
fi

# Get repository information
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
if [ -z "$REPO" ]; then
    echo -e "${RED}Error: Not in a GitHub repository${NC}"
    exit 1
fi

echo -e "${GREEN}Setting up secrets for repository: $REPO${NC}"
echo ""

# Function to set a secret
set_secret() {
    local SECRET_NAME=$1
    local SECRET_DESC=$2
    local SECRET_FILE=$3
    
    echo -e "\n${YELLOW}Setting up $SECRET_NAME${NC}"
    echo "Description: $SECRET_DESC"
    
    if [ -n "$SECRET_FILE" ] && [ -f "$SECRET_FILE" ]; then
        # Secret from file
        echo "Reading from file: $SECRET_FILE"
        gh secret set $SECRET_NAME < "$SECRET_FILE"
        echo -e "${GREEN}✓ $SECRET_NAME set from file${NC}"
    else
        # Secret from user input
        echo "Please enter the value for $SECRET_NAME:"
        read -s SECRET_VALUE
        echo ""
        echo -n "$SECRET_VALUE" | gh secret set $SECRET_NAME
        echo -e "${GREEN}✓ $SECRET_NAME set${NC}"
    fi
}

# Step 1: Set GCP Service Account Key
GCP_KEY_FILE="./gcp-service-account-key.json"
if [ -f "$GCP_KEY_FILE" ]; then
    set_secret "GCP_SA_KEY" "GCP Service Account JSON key for deployment" "$GCP_KEY_FILE"
else
    echo -e "${RED}Warning: $GCP_KEY_FILE not found${NC}"
    echo "Run ./scripts/setup_gcp.sh first to create the service account key"
    echo "Or manually enter the JSON key:"
    set_secret "GCP_SA_KEY" "GCP Service Account JSON key for deployment" ""
fi

# Step 2: Optional - Set other secrets if needed
echo -e "\n${YELLOW}Optional: Set additional secrets${NC}"
echo "These can also be managed through GCP Secret Manager"
read -p "Do you want to set additional secrets in GitHub? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # These are optional since we're using GCP Secret Manager
    set_secret "OPENAI_API_KEY" "OpenAI API key (optional - can use Secret Manager)" ""
    set_secret "MEM0_API_KEY" "Mem0 API key (optional - can use Secret Manager)" ""
    set_secret "AGENT_PRIVATE_KEY" "Agent wallet private key (optional - can use Secret Manager)" ""
fi

# Step 3: Verify secrets
echo -e "\n${GREEN}Verifying secrets...${NC}"
SECRETS=$(gh secret list)
echo "$SECRETS"

# Summary
echo -e "\n${GREEN}=== GitHub Secrets Setup Complete! ===${NC}"
echo ""
echo "Required secret configured:"
echo "  ✓ GCP_SA_KEY - Used for deploying to Google Cloud"
echo ""
echo "Next steps:"
echo "1. Ensure your API keys are in GCP Secret Manager"
echo "2. Update .env.production with your configuration"
echo "3. Push to main branch to trigger deployment"
echo ""
echo -e "${GREEN}Your GitHub Actions workflow is ready! 🚀${NC}"