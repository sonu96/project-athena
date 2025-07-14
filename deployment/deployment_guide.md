# Athena DeFi Agent - Production Deployment Guide

This guide provides comprehensive instructions for deploying the Athena DeFi Agent to Google Cloud Platform in production.

## Prerequisites

### Required Tools
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (gcloud CLI)
- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- [Docker](https://docs.docker.com/get-docker/)
- Python 3.9+ (for local testing)

### Required Accounts & Services
- Google Cloud Platform account with billing enabled
- GCP project with appropriate permissions
- Anthropic API account (for Claude)
- LangSmith account (optional, for monitoring)
- Mem0 account (for memory system)
- CDP (Coinbase Developer Platform) account

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-org/athena-defi-agent.git
cd athena-defi-agent

# Set environment variables
export GCP_PROJECT_ID="your-gcp-project-id"
export GCP_REGION="us-central1"
export TERRAFORM_STATE_BUCKET="your-terraform-state-bucket"
```

### 2. Authentication

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs (first time only)
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  firestore.googleapis.com \
  bigquery.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  run.googleapis.com
```

### 3. Configure Secrets

```bash
# Store API keys in Secret Manager
gcloud secrets create anthropic-api-key --data-file=<(echo -n "your-anthropic-key")
gcloud secrets create langsmith-api-key --data-file=<(echo -n "your-langsmith-key")
gcloud secrets create mem0-api-key --data-file=<(echo -n "your-mem0-key")
gcloud secrets create cdp-api-key-name --data-file=<(echo -n "your-cdp-key-name")
gcloud secrets create cdp-api-key-secret --data-file=<(echo -n "your-cdp-key-secret")
```

### 4. Deploy

```bash
# Run the automated deployment script
./deployment/deploy_production.sh
```

## Manual Deployment Steps

If you prefer manual deployment or need to troubleshoot:

### Step 1: Infrastructure Deployment

```bash
cd deployment/terraform

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize Terraform
terraform init \
  -backend-config="bucket=$TERRAFORM_STATE_BUCKET" \
  -backend-config="prefix=production/terraform.tfstate"

# Plan and apply
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### Step 2: Build and Push Docker Image

```bash
# Build the image
docker build -t gcr.io/$GCP_PROJECT_ID/athena-agent:latest .

# Configure Docker for GCR
gcloud auth configure-docker

# Push the image
docker push gcr.io/$GCP_PROJECT_ID/athena-agent:latest
```

### Step 3: Deploy Cloud Functions

```bash
# Market Data Collector
cd cloud_functions/market_data_collector
gcloud functions deploy market-data-collector \
  --runtime python311 \
  --trigger-http \
  --memory 256MB \
  --timeout 60s \
  --region $GCP_REGION \
  --service-account athena-defi-agent-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Hourly Analysis
cd ../hourly_analysis
gcloud functions deploy hourly-analysis \
  --runtime python311 \
  --trigger-http \
  --memory 256MB \
  --timeout 120s \
  --region $GCP_REGION \
  --service-account athena-defi-agent-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Daily Summary
cd ../daily_summary
gcloud functions deploy daily-summary \
  --runtime python311 \
  --trigger-http \
  --memory 512MB \
  --timeout 300s \
  --region $GCP_REGION \
  --service-account athena-defi-agent-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

### Step 4: Deploy Main Agent

```bash
# Deploy to Cloud Run
gcloud run deploy athena-agent \
  --image gcr.io/$GCP_PROJECT_ID/athena-agent:latest \
  --region $GCP_REGION \
  --service-account athena-defi-agent-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 1 \
  --max-instances 1 \
  --no-allow-unauthenticated
```

## Configuration

### Environment Variables

The agent requires the following environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `GCP_PROJECT_ID` | Your GCP project ID | Yes |
| `FIRESTORE_DATABASE` | Firestore database name | Yes |
| `BIGQUERY_DATASET` | BigQuery dataset name | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `LANGSMITH_API_KEY` | LangSmith API key | No |
| `MEM0_API_KEY` | Mem0 API key | Yes |
| `CDP_API_KEY_NAME` | CDP API key name | Yes |
| `CDP_API_KEY_SECRET` | CDP API key secret | Yes |
| `AGENT_ID` | Unique agent identifier | Yes |
| `AGENT_STARTING_TREASURY` | Starting treasury amount | No (default: 100) |

### Agent Configuration

Key configuration parameters:

```bash
# Agent behavior
AGENT_STARTING_TREASURY=100.0
OBSERVATION_INTERVAL=3600        # 1 hour
EMERGENCY_INTERVAL=7200          # 2 hours in emergency mode

# Cost management
MAX_DAILY_COST=10.0
EMERGENCY_BALANCE_THRESHOLD=25.0

# Network settings
NETWORK=base-sepolia             # Use base-sepolia for testnet
```

## Monitoring & Alerting

### Built-in Monitoring

The deployment includes:

- **Cloud Function monitoring**: Automatic error and latency alerts
- **BigQuery monitoring**: Data quality and ingestion monitoring
- **Agent health checks**: Treasury balance and operational status
- **Cost tracking**: Daily cost monitoring and burn rate alerts

### Accessing Monitoring

1. **Cloud Console**: https://console.cloud.google.com/monitoring?project=YOUR_PROJECT_ID
2. **Logs**: https://console.cloud.google.com/logs?project=YOUR_PROJECT_ID
3. **BigQuery**: https://console.cloud.google.com/bigquery?project=YOUR_PROJECT_ID

### Key Metrics to Monitor

- `athena_agent_treasury_balance`: Current treasury balance
- `athena_agent_emergency_mode`: Emergency mode status (0/1)
- `athena_daily_costs`: Daily operational costs
- `athena_market_data_quality`: Market data quality score
- `athena_decision_confidence`: Agent decision confidence

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Re-authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Permission Errors**
   ```bash
   # Check IAM permissions
   gcloud projects get-iam-policy $GCP_PROJECT_ID
   ```

3. **Function Deployment Failures**
   ```bash
   # Check function logs
   gcloud functions logs read FUNCTION_NAME --region $GCP_REGION
   ```

4. **Memory Formation Issues**
   - Verify Mem0 API key is correct
   - Check Mem0 service status
   - Review memory formation logs

5. **Market Data Collection Issues**
   - Check external API rate limits
   - Verify internet connectivity from Cloud Functions
   - Review data quality scores

### Debugging Commands

```bash
# View recent logs
gcloud logging read "resource.type=\"cloud_function\"" --limit=50

# Check BigQuery data
bq query --use_legacy_sql=false "SELECT * FROM \`$GCP_PROJECT_ID.athena_defi_agent.market_data\` ORDER BY timestamp DESC LIMIT 10"

# Test function directly
gcloud functions call FUNCTION_NAME --region $GCP_REGION

# Check agent status
gcloud run services describe athena-agent --region $GCP_REGION
```

## Maintenance

### Regular Tasks

1. **Weekly**: Review agent performance and cost metrics
2. **Monthly**: Update dependencies and security patches
3. **Quarterly**: Review and optimize model selection and costs

### Scaling Considerations

- **Increase treasury**: Modify `AGENT_STARTING_TREASURY` for longer operation
- **Adjust observation frequency**: Modify `OBSERVATION_INTERVAL` based on market conditions
- **Cost optimization**: Review and adjust model selection thresholds

### Backup & Recovery

- **Infrastructure**: Terraform state is backed up in GCS
- **Data**: BigQuery provides automatic backups
- **Memory**: Mem0 handles memory persistence
- **Firestore**: Automatic multi-region replication

## Security Considerations

### Secret Management
- All API keys stored in Google Secret Manager
- Service account with minimal required permissions
- No secrets in environment variables or code

### Network Security
- Cloud Functions run in Google's secure environment
- No public endpoints for the main agent
- VPC configuration available for enhanced security

### Data Privacy
- All market data is public information
- No personal or sensitive data processed
- Compliance with data retention policies

## Support & Maintenance

### Getting Help

1. **Documentation**: Check this guide and the main README
2. **Logs**: Always check Cloud Logging for detailed error information
3. **Monitoring**: Use Cloud Monitoring dashboards for operational insights
4. **GitHub Issues**: Report bugs and feature requests

### Emergency Procedures

1. **Agent Stuck**: Restart Cloud Run service
2. **High Costs**: Reduce observation frequency or pause operations
3. **Data Issues**: Check BigQuery and Firestore for data integrity
4. **API Limits**: Review rate limiting and implement backoff strategies

---

For additional support, please refer to the project documentation or open an issue on GitHub.