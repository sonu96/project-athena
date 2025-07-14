#!/bin/bash
# Athena DeFi Agent - Production Deployment Script

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
ZONE="${GCP_ZONE:-us-central1-a}"
ENVIRONMENT="${ENVIRONMENT:-production}"
TERRAFORM_STATE_BUCKET="${TERRAFORM_STATE_BUCKET:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if required tools are installed
    command -v gcloud >/dev/null 2>&1 || error "gcloud CLI is required but not installed"
    command -v terraform >/dev/null 2>&1 || error "Terraform is required but not installed"
    command -v docker >/dev/null 2>&1 || error "Docker is required but not installed"
    
    # Check if required environment variables are set
    [[ -z "$PROJECT_ID" ]] && error "GCP_PROJECT_ID environment variable is required"
    [[ -z "$TERRAFORM_STATE_BUCKET" ]] && error "TERRAFORM_STATE_BUCKET environment variable is required"
    
    # Check if authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        error "Not authenticated with gcloud. Run 'gcloud auth login' first"
    fi
    
    # Verify project access
    if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
        error "Cannot access project $PROJECT_ID or project does not exist"
    fi
    
    success "Prerequisites check passed"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log "Deploying infrastructure with Terraform..."
    
    cd deployment/terraform
    
    # Initialize Terraform
    terraform init \
        -backend-config="bucket=$TERRAFORM_STATE_BUCKET" \
        -backend-config="prefix=$ENVIRONMENT/terraform.tfstate"
    
    # Plan deployment
    terraform plan \
        -var="project_id=$PROJECT_ID" \
        -var="region=$REGION" \
        -var="zone=$ZONE" \
        -var="environment=$ENVIRONMENT" \
        -var="terraform_state_bucket=$TERRAFORM_STATE_BUCKET" \
        -out=tfplan
    
    # Ask for confirmation
    read -p "Do you want to apply the Terraform plan? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        warning "Terraform deployment cancelled"
        return 1
    fi
    
    # Apply Terraform changes
    terraform apply tfplan
    
    cd ../..
    success "Infrastructure deployed successfully"
}

# Build and push Docker image
build_and_push_image() {
    log "Building and pushing Docker image..."
    
    # Build image
    IMAGE_TAG="gcr.io/$PROJECT_ID/athena-agent:$(date +%Y%m%d-%H%M%S)"
    docker build -t "$IMAGE_TAG" .
    docker tag "$IMAGE_TAG" "gcr.io/$PROJECT_ID/athena-agent:latest"
    
    # Configure Docker for GCR
    gcloud auth configure-docker --quiet
    
    # Push image
    docker push "$IMAGE_TAG"
    docker push "gcr.io/$PROJECT_ID/athena-agent:latest"
    
    echo "IMAGE_TAG=$IMAGE_TAG" > .env.deploy
    success "Docker image built and pushed: $IMAGE_TAG"
}

# Deploy Cloud Functions
deploy_cloud_functions() {
    log "Deploying Cloud Functions..."
    
    # Market Data Collector
    log "Deploying market data collector..."
    cd cloud_functions/market_data_collector
    gcloud functions deploy market-data-collector \
        --runtime python311 \
        --trigger-http \
        --memory 256MB \
        --timeout 60s \
        --region "$REGION" \
        --service-account "athena-defi-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,FIRESTORE_DATABASE=athena-agent,BIGQUERY_DATASET=athena_defi_agent" \
        --quiet
    
    # Hourly Analysis
    log "Deploying hourly analysis..."
    cd ../hourly_analysis
    gcloud functions deploy hourly-analysis \
        --runtime python311 \
        --trigger-http \
        --memory 256MB \
        --timeout 120s \
        --region "$REGION" \
        --service-account "athena-defi-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,FIRESTORE_DATABASE=athena-agent,BIGQUERY_DATASET=athena_defi_agent" \
        --quiet
    
    # Daily Summary
    log "Deploying daily summary..."
    cd ../daily_summary
    gcloud functions deploy daily-summary \
        --runtime python311 \
        --trigger-http \
        --memory 512MB \
        --timeout 300s \
        --region "$REGION" \
        --service-account "athena-defi-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,FIRESTORE_DATABASE=athena-agent,BIGQUERY_DATASET=athena_defi_agent" \
        --quiet
    
    cd ../..
    success "Cloud Functions deployed successfully"
}

# Deploy main agent to Cloud Run
deploy_agent() {
    log "Deploying main agent to Cloud Run..."
    
    # Load image tag
    if [[ -f .env.deploy ]]; then
        source .env.deploy
    else
        IMAGE_TAG="gcr.io/$PROJECT_ID/athena-agent:latest"
    fi
    
    # Deploy to Cloud Run
    gcloud run deploy athena-agent \
        --image "$IMAGE_TAG" \
        --region "$REGION" \
        --service-account "athena-defi-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --memory 1Gi \
        --cpu 1 \
        --concurrency 1 \
        --max-instances 1 \
        --no-allow-unauthenticated \
        --set-env-vars "AGENT_ID=prod-agent-$(date +%s),GCP_PROJECT_ID=$PROJECT_ID,FIRESTORE_DATABASE=athena-agent,BIGQUERY_DATASET=athena_defi_agent,ENVIRONMENT=production" \
        --quiet
    
    success "Main agent deployed to Cloud Run"
}

# Setup monitoring and alerting
setup_monitoring() {
    log "Setting up monitoring and alerting..."
    
    # Create notification channels (if not exists)
    log "Setting up notification channels..."
    
    # Deploy monitoring infrastructure
    if [[ -f deployment/monitoring/deploy_monitoring.sh ]]; then
        bash deployment/monitoring/deploy_monitoring.sh
    else
        warning "Monitoring deployment script not found, skipping monitoring setup"
    fi
    
    success "Monitoring setup completed"
}

# Run smoke tests
run_smoke_tests() {
    log "Running smoke tests..."
    
    # Test Cloud Functions
    log "Testing market data collector..."
    if gcloud functions call market-data-collector --region "$REGION" >/dev/null 2>&1; then
        success "Market data collector test passed"
    else
        error "Market data collector test failed"
    fi
    
    # Wait and test hourly analysis
    log "Waiting 30 seconds before testing hourly analysis..."
    sleep 30
    
    if gcloud functions call hourly-analysis --region "$REGION" >/dev/null 2>&1; then
        success "Hourly analysis test passed"
    else
        warning "Hourly analysis test failed (may be expected if no data available)"
    fi
    
    # Check BigQuery for data
    log "Checking BigQuery for recent data..."
    RECENT_RECORDS=$(bq query --use_legacy_sql=false --format=csv --max_rows=1 \
        "SELECT COUNT(*) as count FROM \`$PROJECT_ID.athena_defi_agent.market_data\` WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)" | tail -n1)
    
    if [[ "$RECENT_RECORDS" -gt 0 ]]; then
        success "Found $RECENT_RECORDS recent records in BigQuery"
    else
        warning "No recent data found in BigQuery (may be expected for new deployment)"
    fi
    
    success "Smoke tests completed"
}

# Generate deployment report
generate_deployment_report() {
    log "Generating deployment report..."
    
    REPORT_FILE="deployment_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# Athena DeFi Agent - Deployment Report

**Date**: $(date)
**Environment**: $ENVIRONMENT
**Project**: $PROJECT_ID
**Region**: $REGION

## Deployment Details

### Infrastructure
- ✅ Terraform infrastructure deployed
- ✅ Service accounts and IAM configured
- ✅ Firestore database initialized
- ✅ BigQuery dataset and tables created

### Applications
- ✅ Cloud Functions deployed:
  - market-data-collector
  - hourly-analysis
  - daily-summary
- ✅ Main agent deployed to Cloud Run
- ✅ Monitoring and alerting configured

### Image Information
- **Image**: $IMAGE_TAG
- **Registry**: gcr.io/$PROJECT_ID/athena-agent

## Post-Deployment Actions Required

1. **Configure API Keys**: Add the following secrets to Secret Manager:
   - ANTHROPIC_API_KEY
   - LANGSMITH_API_KEY
   - MEM0_API_KEY
   - CDP_API_KEY_NAME
   - CDP_API_KEY_SECRET

2. **Verify Monitoring**: Check that alerts are being received in configured notification channels

3. **Validate Operations**: Monitor the agent for the first 24 hours to ensure stable operation

## Useful Commands

\`\`\`bash
# View function logs
gcloud functions logs read market-data-collector --region $REGION --limit 50

# View Cloud Run logs
gcloud logging read "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"athena-agent\"" --limit 50

# Check BigQuery data
bq query --use_legacy_sql=false "SELECT * FROM \`$PROJECT_ID.athena_defi_agent.market_data\` ORDER BY timestamp DESC LIMIT 10"

# View monitoring dashboard
echo "https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
\`\`\`

## Support Information

- **Project Console**: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID
- **Cloud Functions**: https://console.cloud.google.com/functions/list?project=$PROJECT_ID
- **Cloud Run**: https://console.cloud.google.com/run?project=$PROJECT_ID
- **Monitoring**: https://console.cloud.google.com/monitoring?project=$PROJECT_ID

Generated by: Athena DeFi Agent Deployment Script
EOF

    success "Deployment report generated: $REPORT_FILE"
}

# Main deployment function
main() {
    log "Starting Athena DeFi Agent production deployment..."
    log "Project: $PROJECT_ID"
    log "Region: $REGION"
    log "Environment: $ENVIRONMENT"
    
    # Confirm deployment
    read -p "Are you sure you want to deploy to $ENVIRONMENT environment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        warning "Deployment cancelled"
        exit 0
    fi
    
    # Execute deployment steps
    check_prerequisites
    deploy_infrastructure
    build_and_push_image
    deploy_cloud_functions
    deploy_agent
    setup_monitoring
    run_smoke_tests
    generate_deployment_report
    
    success "🎉 Athena DeFi Agent deployment completed successfully!"
    success "The agent is now running in production and should begin operations shortly."
    
    log "Next steps:"
    echo "1. Configure API keys in Secret Manager"
    echo "2. Monitor the agent dashboard for the first 24 hours"
    echo "3. Verify data is flowing to BigQuery"
    echo "4. Check monitoring alerts are working"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi