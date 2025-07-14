#!/bin/bash

# Project Athena - Quick Deployment Script
# This script runs through the deployment process

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Project Athena Deployment Script ===${NC}"
echo "This script will guide you through the deployment process"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt for continuation
prompt_continue() {
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deployment paused. You can resume anytime.${NC}"
        exit 0
    fi
}

# Step 1: Check prerequisites
echo -e "${GREEN}Step 1: Checking prerequisites${NC}"
MISSING_TOOLS=()

if ! command_exists gcloud; then
    MISSING_TOOLS+=("gcloud (Google Cloud SDK)")
fi

if ! command_exists docker; then
    MISSING_TOOLS+=("docker")
fi

if ! command_exists gh; then
    MISSING_TOOLS+=("gh (GitHub CLI)")
fi

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo -e "${RED}Missing required tools:${NC}"
    printf '%s\n' "${MISSING_TOOLS[@]}"
    echo ""
    echo "Please install missing tools and run again."
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites installed${NC}"
echo ""

# Step 2: GCP Setup
echo -e "${GREEN}Step 2: GCP Project Setup${NC}"
if [ -f "gcp-service-account-key.json" ]; then
    echo -e "${YELLOW}GCP service account key already exists${NC}"
else
    echo "Running GCP setup script..."
    prompt_continue
    ./scripts/setup_gcp.sh
fi
echo ""

# Step 3: GitHub Secrets
echo -e "${GREEN}Step 3: GitHub Secrets Setup${NC}"
echo "Checking GitHub authentication..."
if gh auth status &> /dev/null; then
    echo -e "${GREEN}✓ GitHub CLI authenticated${NC}"
    echo "Setting up GitHub secrets..."
    prompt_continue
    ./scripts/setup_github_secrets.sh
else
    echo -e "${RED}GitHub CLI not authenticated${NC}"
    echo "Please run: gh auth login"
    exit 1
fi
echo ""

# Step 4: Secret Manager
echo -e "${GREEN}Step 4: Secret Manager Setup${NC}"
echo "Setting up GCP Secret Manager..."
prompt_continue
./scripts/setup_secrets.sh
echo ""

# Step 5: Local Testing
echo -e "${GREEN}Step 5: Local Testing${NC}"
echo "Would you like to test locally first?"
read -p "Run local tests? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Building Docker image..."
    docker build -t athena-agent-test .
    
    echo -e "${GREEN}✓ Docker build successful${NC}"
    echo ""
    echo "To run locally:"
    echo "  docker-compose up"
    echo ""
fi

# Step 6: Deploy
echo -e "${GREEN}Step 6: Deploy to Cloud Run${NC}"
echo -e "${YELLOW}You have two options:${NC}"
echo "1. Push to main branch (recommended) - GitHub Actions will deploy"
echo "2. Manual deployment using gcloud"
echo ""
echo "Which option? (1/2)"
read -p "Choice: " DEPLOY_CHOICE

case $DEPLOY_CHOICE in
    1)
        echo -e "${GREEN}Preparing for GitHub Actions deployment${NC}"
        echo "Make sure you have:"
        echo "  - Committed all changes"
        echo "  - Set up GitHub secrets (GCP_SA_KEY)"
        echo ""
        echo "Ready to push to main?"
        prompt_continue
        
        git add .
        git commit -m "Deploy: Initial deployment to Cloud Run" || true
        git push origin main
        
        echo -e "${GREEN}✓ Pushed to main branch${NC}"
        echo "Check GitHub Actions for deployment progress:"
        echo "  https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions"
        ;;
    2)
        echo -e "${GREEN}Manual deployment to Cloud Run${NC}"
        prompt_continue
        
        PROJECT_ID="project-athena-personal"
        SERVICE_NAME="athena-agent"
        REGION="us-central1"
        
        echo "Building and deploying..."
        gcloud run deploy $SERVICE_NAME \
            --source . \
            --platform managed \
            --region $REGION \
            --project $PROJECT_ID \
            --allow-unauthenticated
        
        echo -e "${GREEN}✓ Deployed to Cloud Run${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Step 7: Verify Deployment
echo ""
echo -e "${GREEN}Step 7: Verify Deployment${NC}"
echo "Waiting for deployment to complete..."
sleep 10

PROJECT_ID="project-athena-personal"
SERVICE_NAME="athena-agent"
REGION="us-central1"

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --format 'value(status.url)' 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
    echo -e "${GREEN}✓ Service deployed successfully!${NC}"
    echo "Service URL: $SERVICE_URL"
    echo ""
    echo "Testing health endpoint..."
    curl -s "$SERVICE_URL/health" | jq . || echo "Health check response received"
    echo ""
    
    # Save service URL
    echo "$SERVICE_URL" > .service-url
    echo -e "${GREEN}Service URL saved to .service-url${NC}"
else
    echo -e "${RED}Could not retrieve service URL${NC}"
    echo "Check the deployment status in Cloud Console"
fi

# Step 8: Post-deployment
echo ""
echo -e "${GREEN}Step 8: Post-Deployment Setup${NC}"
echo "1. Set up budget alerts in Cloud Console"
echo "2. Configure monitoring dashboards"
echo "3. Activate scheduled tasks (treasury check, market scan)"
echo "4. Test all API endpoints"
echo ""

# Summary
echo -e "${BLUE}=== Deployment Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Check the deployment checklist: deployment/deployment_checklist.md"
echo "2. Monitor initial costs and performance"
echo "3. Set up automation schedules"
echo "4. Update documentation with service URL"
echo ""
echo -e "${GREEN}Your personal DeFi agent is now live! 🚀${NC}"

# Create summary file
cat > deployment-summary.txt << EOF
Deployment Summary
==================
Date: $(date)
Project ID: $PROJECT_ID
Service Name: $SERVICE_NAME
Region: $REGION
Service URL: $SERVICE_URL

Deployed Features:
- Enhanced Mem0 memory system
- Treasury monitoring with alerts
- Personal dashboard API
- Automated scheduled tasks
- WebSocket real-time updates

Configuration:
- Cost budget: \$50/month
- Min instances: 0 (scales to zero)
- Max instances: 3
- Memory: 512Mi
- CPU: 1

Security:
- Secrets in Secret Manager
- Service account with minimal permissions
- No secrets in code

Next Steps:
1. Activate automations
2. Monitor costs
3. Test all endpoints
EOF

echo ""
echo "Deployment summary saved to: deployment-summary.txt"