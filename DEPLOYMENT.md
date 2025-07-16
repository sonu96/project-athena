# Athena Agent - Deployment Guide

This guide walks through deploying Athena Agent to Google Cloud Run for 24/7 operation on BASE mainnet.

## Prerequisites

1. Google Cloud account with billing enabled
2. `gcloud` CLI installed and authenticated
3. Docker installed locally
4. All API keys ready (CDP, Mem0, LangSmith)

## Step 1: Google Cloud Setup

```bash
# Set your project ID
export PROJECT_ID="project-athena-development"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  bigquery.googleapis.com \
  firestore.googleapis.com \
  containerregistry.googleapis.com

# Run setup script
./setup_gcp.sh
```

## Step 2: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create athena-agent-sa \
  --display-name="Athena Agent Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:athena-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:athena-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:athena-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Download service account key
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=athena-agent-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Step 3: Test Locally with Mainnet

```bash
# Copy mainnet configuration
cp .env.mainnet .env

# Run basic test
python3 test_mainnet_simple.py

# Run full test
python3 test_mainnet.py

# Run continuous test (10 minutes)
python3 test_mainnet.py --continuous 10
```

## Step 4: Build and Push Docker Image

```bash
# Build image
docker build -t gcr.io/$PROJECT_ID/athena-agent:latest .

# Test locally
docker run --env-file .env gcr.io/$PROJECT_ID/athena-agent:latest

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/athena-agent:latest
```

## Step 5: Deploy to Cloud Run

```bash
# Deploy using script
./deploy_cloud.sh

# Or manually deploy
gcloud run deploy athena-agent-mainnet \
  --image gcr.io/$PROJECT_ID/athena-agent:latest \
  --region us-central1 \
  --platform managed \
  --service-account athena-agent-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 3 \
  --min-instances 1 \
  --set-env-vars "ENVIRONMENT=production,NETWORK=base,OBSERVATION_MODE=true" \
  --set-secrets "CDP_API_KEY_NAME=cdp-api-key-name:latest,CDP_API_KEY_SECRET=cdp-api-key-secret:latest,MEM0_API_KEY=mem0-api-key:latest,LANGSMITH_API_KEY=langsmith-api-key:latest" \
  --allow-unauthenticated
```

## Step 6: Monitoring

### View Logs
```bash
# Recent logs
gcloud logging read "resource.labels.service_name=athena-agent-mainnet" --limit=50

# Follow logs
gcloud alpha logging tail "resource.labels.service_name=athena-agent-mainnet"
```

### Check Service Status
```bash
# Get service details
gcloud run services describe athena-agent-mainnet --region us-central1

# Get service URL
SERVICE_URL=$(gcloud run services describe athena-agent-mainnet --region us-central1 --format 'value(status.url)')
echo "Service URL: $SERVICE_URL"

# Health check
curl $SERVICE_URL/health
```

### View Metrics
- Cloud Run metrics: https://console.cloud.google.com/run/detail/us-central1/athena-agent-mainnet/metrics
- BigQuery data: https://console.cloud.google.com/bigquery
- LangSmith traces: https://smith.langchain.com

## Step 7: Verify Production Operation

1. Check agent is running:
```bash
curl $SERVICE_URL/agent/status
```

2. View recent memories:
```bash
curl $SERVICE_URL/agent/memories?limit=10
```

3. Check BigQuery for data:
```sql
-- In BigQuery console
SELECT * FROM athena_analytics.agent_metrics
ORDER BY timestamp DESC
LIMIT 10;
```

## Troubleshooting

### Common Issues

1. **Service account permissions**
   - Ensure all IAM roles are granted
   - Check service account key is valid

2. **Secret access errors**
   - Verify secrets exist in Secret Manager
   - Check service account has secretAccessor role

3. **Memory/CPU limits**
   - Monitor Cloud Run metrics
   - Increase limits if needed

4. **CDP wallet issues**
   - Ensure wallet has ETH for gas
   - Check CDP API keys are correct

### Debug Commands

```bash
# Check service logs for errors
gcloud logging read "resource.labels.service_name=athena-agent-mainnet AND severity>=ERROR" --limit=20

# View container startup logs
gcloud run services logs athena-agent-mainnet --region us-central1

# Check BigQuery for recent activity
bq query --use_legacy_sql=false \
  'SELECT * FROM athena_analytics.agent_metrics ORDER BY timestamp DESC LIMIT 5'
```

## Production Checklist

- [ ] All API keys configured in Secret Manager
- [ ] Service account created with proper permissions
- [ ] BigQuery dataset and tables created
- [ ] Docker image built and pushed
- [ ] Cloud Run service deployed
- [ ] Health endpoint responding
- [ ] Logs showing cognitive cycles
- [ ] BigQuery receiving data
- [ ] LangSmith showing traces
- [ ] Wallet has sufficient ETH for gas

## Cost Optimization

1. **Adjust cycle frequency** in environment variables
2. **Use appropriate LLM models** based on emotional state
3. **Monitor BigQuery storage** and implement data retention
4. **Set Cloud Run max instances** to control scaling

## Next Steps

1. Monitor agent performance for 24 hours
2. Review memory formation patterns
3. Analyze cost per cycle
4. Prepare for V2 trading implementation

---

For support, check logs and metrics dashboards. The agent is designed to be self-healing and will restart automatically on failures.