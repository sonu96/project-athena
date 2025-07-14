# Project Athena - Deployment Checklist

This checklist ensures all steps are completed for successful deployment.

## Pre-Deployment Setup

### 1. GCP Project Setup ✓
Run: `./scripts/setup_gcp.sh`

- [ ] GCP account created
- [ ] Billing enabled
- [ ] Project created: `project-athena-personal`
- [ ] APIs enabled:
  - [ ] Cloud Run API
  - [ ] Cloud Build API
  - [ ] Secret Manager API
  - [ ] Firestore API
  - [ ] Cloud Storage API
  - [ ] Container Registry API
- [ ] Service account created: `athena-deployer`
- [ ] Service account key downloaded: `gcp-service-account-key.json`
- [ ] Firestore database created
- [ ] Cloud Storage bucket created

### 2. GitHub Secrets Configuration ✓
Run: `./scripts/setup_github_secrets.sh`

- [ ] GitHub CLI installed
- [ ] Authenticated with GitHub
- [ ] Secret added: `GCP_SA_KEY` (service account JSON)

### 3. GCP Secret Manager ✓
Run: `./scripts/setup_secrets.sh`

- [ ] Secret created: `openai-api-key`
- [ ] Secret created: `mem0-api-key`
- [ ] Secret created: `agent-private-key`
- [ ] Cloud Run granted access to secrets

### 4. Environment Configuration ✓
- [ ] `.env.production` updated with project-specific values
- [ ] `.env.production.local` created (for local testing only)
- [ ] `.gitignore` includes sensitive files

## Deployment Steps

### 5. Local Testing
```bash
# Build and test locally
docker-compose up --build

# Run tests
pytest tests/

# Test API endpoints
curl http://localhost:8080/health
curl http://localhost:8080/api/personal/dashboard
```

- [ ] Docker builds successfully
- [ ] Application starts without errors
- [ ] Health check passes
- [ ] API endpoints respond

### 6. Deploy to Cloud Run
```bash
# Option 1: Push to main branch (automatic deployment)
git add .
git commit -m "Deploy: Initial deployment to Cloud Run"
git push origin main

# Option 2: Manual deployment
gcloud run deploy athena-agent \
  --source . \
  --platform managed \
  --region us-central1 \
  --project project-athena-personal
```

- [ ] GitHub Actions workflow runs successfully
- [ ] Docker image built and pushed
- [ ] Cloud Run service deployed
- [ ] Service URL obtained

### 7. Post-Deployment Verification

- [ ] Access service URL and check health endpoint
- [ ] Verify logs in Cloud Console
- [ ] Test API endpoints:
  ```bash
  SERVICE_URL=$(gcloud run services describe athena-agent --region us-central1 --format 'value(status.url)')
  curl $SERVICE_URL/health
  curl $SERVICE_URL/api/personal/dashboard
  ```
- [ ] Check Secret Manager integration
- [ ] Verify Firestore connection
- [ ] Monitor initial costs

## Configuration Verification

### 8. Budget & Alerts
- [ ] Budget alert set at $25 (50% of $50 limit)
- [ ] Budget alert set at $40 (80% of $50 limit)
- [ ] Email notifications configured

### 9. Monitoring Setup
- [ ] Cloud Logging enabled
- [ ] Cloud Monitoring dashboard created
- [ ] Uptime checks configured
- [ ] Error reporting enabled

### 10. Security Review
- [ ] No secrets in code repository
- [ ] Service account has minimum required permissions
- [ ] Cloud Run service using authenticated invocations (if needed)
- [ ] Firestore security rules configured

## Operational Tasks

### 11. Documentation
- [ ] Update README with deployment instructions
- [ ] Document service URL
- [ ] Create runbook for common operations
- [ ] Update team on deployment status

### 12. Automation Activation
```bash
# After deployment, activate scheduled tasks
curl -X POST $SERVICE_URL/api/automation/schedule/treasury-check
curl -X POST $SERVICE_URL/api/automation/schedule/market-scan
```

- [ ] Treasury check scheduled
- [ ] Market scan scheduled
- [ ] Memory optimization scheduled

## Troubleshooting Checklist

If deployment fails, check:

- [ ] All required APIs are enabled
- [ ] Service account has correct permissions
- [ ] Secrets are properly configured
- [ ] Environment variables are set
- [ ] Docker image builds locally
- [ ] GitHub Actions has correct secrets

## Rollback Plan

If issues occur:

1. **Immediate**: Stop Cloud Run service
   ```bash
   gcloud run services update athena-agent --no-traffic --region us-central1
   ```

2. **Revert**: Deploy previous version
   ```bash
   gcloud run deploy athena-agent --image gcr.io/project-athena-personal/athena-agent:previous-tag
   ```

3. **Investigate**: Check logs and monitoring

## Success Criteria

- [ ] Service responds to health checks
- [ ] Dashboard API returns data
- [ ] No error logs in first hour
- [ ] Cost projections under $50/month
- [ ] All automated tasks scheduled

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Service URL**: _______________  
**Notes**: _______________