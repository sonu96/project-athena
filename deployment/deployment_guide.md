# Project Athena - Deployment Guide

## Prerequisites

1. **Google Cloud Account**
   - Create a GCP project: `project-athena-personal`
   - Enable required APIs:
     ```bash
     gcloud services enable \
       run.googleapis.com \
       cloudbuild.googleapis.com \
       secretmanager.googleapis.com \
       firestore.googleapis.com \
       storage.googleapis.com
     ```

2. **GitHub Repository**
   - Fork/clone the repository
   - Set up GitHub secrets (Settings > Secrets):
     - `GCP_SA_KEY`: Service account JSON key

3. **Local Development Tools**
   - Docker Desktop installed
   - gcloud CLI installed and configured
   - Python 3.11+

## Initial Setup

### 1. Create GCP Service Account

```bash
# Create service account
gcloud iam service-accounts create athena-deployer \
  --display-name="Athena Deployer"

# Grant necessary permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:athena-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:athena-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:athena-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"

# Download key
gcloud iam service-accounts keys create key.json \
  --iam-account=athena-deployer@PROJECT_ID.iam.gserviceaccount.com
```

### 2. Set Up Secrets in Secret Manager

```bash
# Create secrets
echo -n "your-openai-key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your-mem0-key" | gcloud secrets create mem0-api-key --data-file=-
echo -n "your-private-key" | gcloud secrets create agent-private-key --data-file=-
```

### 3. Configure Firestore

```bash
# Create Firestore database
gcloud firestore databases create --region=us-central
```

### 4. Create Cloud Storage Bucket

```bash
# Create bucket for backups
gsutil mb -p PROJECT_ID -l us-central1 gs://project-athena-storage/
```

## Local Development

### 1. Build and Run Locally

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your development values

# Build and run with Docker Compose
docker-compose up --build
```

### 2. Test the Application

```bash
# Health check
curl http://localhost:8080/health

# Get agent state
curl http://localhost:8080/agent/state
```

## Deployment

### 1. Manual Deployment

```bash
# Build and push image
docker build -t gcr.io/PROJECT_ID/athena-agent:latest .
docker push gcr.io/PROJECT_ID/athena-agent:latest

# Deploy to Cloud Run
gcloud run deploy athena-agent \
  --image gcr.io/PROJECT_ID/athena-agent:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 2. Automated Deployment

Simply push to the main branch:
```bash
git add .
git commit -m "Deploy: your message"
git push origin main
```

GitHub Actions will automatically:
1. Run tests
2. Build Docker image
3. Push to GCR
4. Deploy to Cloud Run

## Monitoring

### 1. View Logs

```bash
# Stream logs
gcloud run logs tail athena-agent --region=us-central1

# View in console
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=athena-agent" --limit 50
```

### 2. Check Service Status

```bash
# Get service details
gcloud run services describe athena-agent --region=us-central1

# Get service URL
gcloud run services describe athena-agent --region=us-central1 --format='value(status.url)'
```

## Cost Optimization

1. **Cloud Run Settings**
   - Min instances: 0 (scales to zero)
   - Max instances: 3 (prevent runaway costs)
   - Memory: 512Mi (sufficient for agent)
   - CPU: 1 (can increase if needed)

2. **Firestore**
   - Use batch operations
   - Implement caching
   - Clean up old data regularly

3. **Monitoring**
   - Set up budget alerts at $25 and $40
   - Review Cloud Run metrics weekly
   - Monitor Firestore usage

## Troubleshooting

### Common Issues

1. **Deploy fails with permission error**
   - Check service account permissions
   - Ensure APIs are enabled

2. **Container crashes on start**
   - Check environment variables
   - Review logs for missing dependencies

3. **High latency**
   - Check cold start times
   - Consider keeping 1 min instance

4. **Memory errors**
   - Increase Cloud Run memory limit
   - Optimize Mem0 queries

## Security Best Practices

1. **Never commit secrets**
   - Use Secret Manager for all sensitive data
   - Keep .env files out of git

2. **Limit access**
   - Use IAM for team members
   - Enable audit logging

3. **Regular updates**
   - Update dependencies monthly
   - Monitor security advisories

## Maintenance

### Weekly Tasks
- Review logs for errors
- Check cost dashboard
- Verify backups are running

### Monthly Tasks
- Update dependencies
- Review and optimize queries
- Clean up old data
- Security audit