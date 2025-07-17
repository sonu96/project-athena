# GCP Services Stopped - January 17, 2025

## Services Stopped

### 1. Cloud Run Services
- **athena-agent-phase1** (DELETED)
  - URL: https://athena-agent-phase1-835292953759.us-central1.run.app
  - Last deployed: 2025-07-17T06:12:10.383911Z
  - Status: Successfully deleted

### 2. Cloud Scheduler Jobs  
- **collect-aerodrome-pools** (PAUSED)
  - Location: us-central1
  - Schedule: */15 * * * * (Every 15 minutes)
  - Target: HTTP (Cloud Function)
  - Status: Paused (can be resumed later)

### 3. Cloud Functions
- **aerodrome-pool-collector** (DELETED)
  - Region: us-central1
  - Trigger: HTTP
  - Generation: 2nd gen
  - Status: Successfully deleted

## Data Retention
- BigQuery tables remain intact with collected data
- Firestore collections remain available
- No data was deleted, only compute services stopped

## To Restart Services
1. Redeploy Cloud Run service: `./scripts/deploy.sh`
2. Resume scheduler: `gcloud scheduler jobs resume collect-aerodrome-pools --location=us-central1`
3. Redeploy function: See deployment commands in cloud_functions/pool_collector/

## Cost Savings
- Cloud Run: ~$0/month when not running
- Cloud Functions: ~$0/month when deleted  
- Cloud Scheduler: ~$0/month when paused
- Storage (BigQuery/Firestore): Minimal ongoing costs remain

## Next Steps
The main design decision needed is whether to:
1. Use CDP SDK properly through the main agent
2. Continue with direct RPC approach
3. Implement a hybrid solution

This will affect how services are redeployed.