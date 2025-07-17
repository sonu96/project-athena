# Athena Agent Phase 1 Production Deployment Guide

## Overview
This guide walks through deploying Athena Agent Phase 1 for 24/7 autonomous operation on Google Cloud Platform.

## Prerequisites

1. **Docker Desktop** must be running
2. **Google Cloud CLI** installed and configured
3. **Service Account** with proper permissions
4. **Environment Variables** configured in `.env`

## Pre-Deployment Checklist

Run the checklist script:
```bash
python3 scripts/pre_deployment_check.py
```

All checks should pass before proceeding.

## Deployment Steps

### Step 1: Start Docker Desktop
Make sure Docker Desktop is running on your machine.

### Step 2: Set Environment Variables
Ensure your `.env` file has all required keys:
- `CDP_API_KEY_NAME` and `CDP_API_KEY_SECRET`
- `MEM0_API_KEY` 
- `LANGSMITH_API_KEY`

### Step 3: Run Deployment Script
```bash
python3 scripts/deploy_production.py
```

This script will:
1. Build and push Docker container
2. Deploy pool collector cloud function (runs every 15 minutes)
3. Deploy main agent to Cloud Run
4. Set up monitoring and health checks

### Step 4: Verify Deployment

After deployment, verify everything is working:

1. **Check Cloud Run Service**
   ```bash
   gcloud run services describe athena-agent-phase1 --region us-central1
   ```

2. **Check Logs**
   ```bash
   gcloud logging read "resource.labels.service_name=athena-agent-phase1" --limit 50
   ```

3. **Verify Pool Collection**
   ```bash
   bq query --use_legacy_sql=false 'SELECT COUNT(*) as count FROM athena_analytics.pool_observations WHERE DATE(timestamp) = CURRENT_DATE()'
   ```

4. **Test Health Endpoint**
   ```bash
   curl https://[YOUR-SERVICE-URL]/health
   ```

## Production Configuration

### Environment Variables (Cloud Run)
- `GCP_PROJECT_ID`: athena-defi-agent-1752635199
- `BIGQUERY_DATASET`: athena_analytics
- `OBSERVATION_MODE`: true (Phase 1 only observes)
- `NETWORK`: base (BASE mainnet)
- `ENV`: production

### Resource Allocation
- **Cloud Run**: 2GB RAM, 1 CPU, min 1 instance
- **Pool Collector**: 512MB RAM, 9 minute timeout
- **Schedule**: Pool data collected every 15 minutes

### Monitoring
- **Health Check**: https://[SERVICE-URL]/health
- **Uptime Check**: Every 5 minutes
- **Logs**: Cloud Logging with structured JSON
- **Metrics**: BigQuery analytics tables

## Cost Estimates

### Monthly Costs (Approximate)
- **Cloud Run**: ~$50-100 (depends on traffic)
- **Cloud Functions**: ~$5-10
- **BigQuery**: ~$5-20 (storage + queries)
- **Total**: ~$60-130/month

### Cost Controls
- Hard $30/day limit on API calls
- Automatic shutdown on budget exceed
- Cost tracking in BigQuery

## Troubleshooting

### Common Issues

1. **Docker build fails**
   - Ensure Docker Desktop is running
   - Check disk space
   - Try `docker system prune`

2. **Deployment fails**
   - Check gcloud authentication: `gcloud auth list`
   - Verify project: `gcloud config get-value project`
   - Check API enablement

3. **No data in BigQuery**
   - Check pool collector logs
   - Verify BASE RPC connectivity
   - Check for rate limiting

4. **Health check fails**
   - Check Cloud Run logs
   - Verify all environment variables
   - Check service account permissions

### Useful Commands

```bash
# View live logs
gcloud run logs read athena-agent-phase1 --tail 50 -f

# Test pool collector
gcloud functions call aerodrome-pool-collector

# Check BigQuery data
bq head athena_analytics.pool_observations

# Update environment variable
gcloud run services update athena-agent-phase1 --set-env-vars KEY=VALUE
```

## Next Steps

After successful deployment:

1. **Monitor First 24 Hours**
   - Check logs every few hours
   - Verify pool data collection
   - Monitor costs

2. **Set Up Dashboards**
   - Create Grafana dashboard
   - Set up alerts for errors
   - Monitor treasury balance

3. **Optimize Performance**
   - Adjust collection frequency if needed
   - Tune memory allocation
   - Optimize BigQuery queries

## Phase 2 Preparation

Once Phase 1 is stable (1-2 weeks), prepare for Phase 2:
- Enable CDP wallet functionality
- Implement trading logic
- Add risk management
- Enhanced monitoring

## Support

- **Logs**: Cloud Logging console
- **Metrics**: BigQuery dashboards
- **Alerts**: Set up in Cloud Monitoring
- **Documentation**: Update as needed

---

Remember: Phase 1 is OBSERVATION ONLY. No trading or financial transactions.