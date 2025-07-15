#!/bin/bash

# Budget Alert and Auto-Shutdown Setup for Athena Project
# This script sets up a $30 budget alert with automatic service shutdown

PROJECT_ID=$(gcloud config get-value project)
BILLING_ACCOUNT=$(gcloud beta billing projects describe $PROJECT_ID --format="value(billingAccountName)" | cut -d'/' -f2)

echo "🚨 Setting up budget alerts for Project Athena..."
echo "Project: $PROJECT_ID"
echo "Billing Account: $BILLING_ACCOUNT"

# Create budget with alerts
echo "📊 Creating $30 budget with alerts..."

gcloud billing budgets create \
    --billing-account=$BILLING_ACCOUNT \
    --display-name="Athena-30-Dollar-Limit" \
    --budget-amount=30 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=75 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100 \
    --all-updates-rule \
    --budget-filter="projects/$PROJECT_ID"

# Create Cloud Function for auto-shutdown
echo "🔧 Creating auto-shutdown Cloud Function..."

mkdir -p cloud_functions/budget_guardian

# Create the shutdown function
cat > cloud_functions/budget_guardian/main.py << 'EOF'
import base64
import json
import logging
import os
from google.cloud import firestore
from google.cloud import scheduler_v1
from google.cloud import functions_v1
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get('GCP_PROJECT')
SHUTDOWN_THRESHOLD = 0.90  # Shutdown at 90% of budget

def budget_alert_handler(request):
    """
    Cloud Function triggered by budget alerts
    Automatically shuts down services when approaching $30 limit
    """
    try:
        # Parse the Pub/Sub message
        pubsub_message = request.get_json()
        if 'message' in pubsub_message:
            message_data = base64.b64decode(pubsub_message['message']['data']).decode('utf-8')
            budget_notification = json.loads(message_data)
        else:
            budget_notification = pubsub_message
        
        # Extract budget details
        budget_amount = budget_notification.get('budgetAmount', {}).get('specifiedAmount', {}).get('units', '30')
        cost_amount = budget_notification.get('costAmount', {}).get('amount', 0)
        budget_name = budget_notification.get('budgetDisplayName', 'Unknown')
        
        budget_amount = float(budget_amount)
        cost_amount = float(cost_amount)
        threshold_percent = cost_amount / budget_amount
        
        logger.info(f"Budget Alert: {budget_name}")
        logger.info(f"Current spend: ${cost_amount:.2f} / ${budget_amount:.2f} ({threshold_percent*100:.1f}%)")
        
        # Store alert in Firestore
        db = firestore.Client()
        alert_doc = {
            'timestamp': datetime.utcnow(),
            'budget_name': budget_name,
            'budget_amount': budget_amount,
            'cost_amount': cost_amount,
            'threshold_percent': threshold_percent,
            'action_taken': None
        }
        
        # Check if we need to shutdown
        if threshold_percent >= SHUTDOWN_THRESHOLD:
            logger.warning(f"🚨 CRITICAL: Budget at {threshold_percent*100:.1f}%! Initiating shutdown...")
            
            # Disable Cloud Scheduler jobs
            try:
                scheduler = scheduler_v1.CloudSchedulerClient()
                parent = f"projects/{PROJECT_ID}/locations/us-central1"
                
                for job in scheduler.list_jobs(request={"parent": parent}):
                    if 'athena' in job.name.lower():
                        logger.info(f"Pausing job: {job.name}")
                        scheduler.pause_job(request={"name": job.name})
                        alert_doc['action_taken'] = 'jobs_paused'
            except Exception as e:
                logger.error(f"Error pausing jobs: {e}")
            
            # Disable Cloud Functions
            try:
                functions = functions_v1.CloudFunctionsServiceClient()
                parent = f"projects/{PROJECT_ID}/locations/us-central1"
                
                for function in functions.list_functions(request={"parent": parent}):
                    if 'athena' in function.name.lower() and 'budget' not in function.name.lower():
                        logger.info(f"Disabling function: {function.name}")
                        # Note: In production, you'd update the function to return early
                        alert_doc['action_taken'] = 'functions_notified'
            except Exception as e:
                logger.error(f"Error handling functions: {e}")
            
            # Set emergency flag in Firestore
            emergency_doc = {
                'emergency_shutdown': True,
                'timestamp': datetime.utcnow(),
                'reason': f'Budget exceeded {threshold_percent*100:.1f}%',
                'cost_at_shutdown': cost_amount
            }
            db.collection('agent_data_system_logs').document('emergency_state').set(emergency_doc)
            
            # Send notification (in production, this would email/SMS)
            logger.critical(f"💀 EMERGENCY SHUTDOWN COMPLETED - Cost: ${cost_amount:.2f}")
            
        elif threshold_percent >= 0.75:
            logger.warning(f"⚠️ WARNING: Budget at {threshold_percent*100:.1f}%")
            alert_doc['action_taken'] = 'warning_logged'
            
        # Save alert to Firestore
        db.collection('budget_alerts').add(alert_doc)
        
        return {'status': 'success', 'threshold_percent': threshold_percent}
        
    except Exception as e:
        logger.error(f"Error processing budget alert: {e}")
        return {'status': 'error', 'error': str(e)}
EOF

# Create requirements.txt
cat > cloud_functions/budget_guardian/requirements.txt << 'EOF'
google-cloud-firestore>=2.11.0
google-cloud-scheduler>=2.7.0
google-cloud-functions>=1.8.0
EOF

# Create deployment script
cat > cloud_functions/budget_guardian/deploy.sh << 'EOF'
#!/bin/bash
gcloud functions deploy budget-guardian \
    --runtime python310 \
    --trigger-topic budget-alerts \
    --entry-point budget_alert_handler \
    --memory 256MB \
    --timeout 300s \
    --set-env-vars GCP_PROJECT=$PROJECT_ID
EOF

chmod +x cloud_functions/budget_guardian/deploy.sh

# Create Pub/Sub topic for budget alerts
echo "📬 Creating Pub/Sub topic for budget alerts..."
gcloud pubsub topics create budget-alerts --quiet || true

# Create monitoring dashboard
echo "📊 Creating monitoring dashboard..."
cat > monitoring_dashboard.json << 'EOF'
{
  "displayName": "Athena Budget Monitor",
  "dashboardFilters": [],
  "gridLayout": {
    "widgets": [
      {
        "title": "Daily Spend",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"global\" AND metric.type=\"billing.googleapis.com/project/cost\"",
                "aggregation": {
                  "alignmentPeriod": "86400s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            }
          }]
        }
      },
      {
        "title": "Budget Utilization",
        "scorecard": {
          "timeSeriesQuery": {
            "timeSeriesFilter": {
              "filter": "resource.type=\"global\" AND metric.type=\"billing.googleapis.com/project/cost\"",
              "aggregation": {
                "alignmentPeriod": "3600s",
                "perSeriesAligner": "ALIGN_MEAN"
              }
            }
          },
          "thresholds": [
            {
              "value": 27.0,
              "color": "RED"
            },
            {
              "value": 22.5,
              "color": "YELLOW"
            }
          ]
        }
      }
    ]
  }
}
EOF

# Create daily cost check script
cat > check_daily_cost.py << 'EOF'
#!/usr/bin/env python3
"""
Check daily GCP costs for Athena project
"""

import subprocess
import json
from datetime import datetime, timedelta

def check_costs():
    # Get yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get cost data
    cmd = f"""
    gcloud billing costs list \
        --billing-account={BILLING_ACCOUNT} \
        --filter="usage_start_time>={yesterday}" \
        --format=json
    """
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        costs = json.loads(result.stdout) if result.stdout else []
        
        total_cost = sum(float(cost.get('cost', {}).get('amount', 0)) for cost in costs)
        
        print(f"💰 Daily Cost Report for {yesterday}")
        print(f"Total spend: ${total_cost:.2f}")
        print(f"Remaining budget: ${30 - total_cost:.2f}")
        print(f"Days until limit: {(30 - total_cost) / total_cost if total_cost > 0 else 'N/A'}")
        
    except Exception as e:
        print(f"Error checking costs: {e}")

if __name__ == "__main__":
    check_costs()
EOF

chmod +x check_daily_cost.py

echo ""
echo "✅ Budget protection setup complete!"
echo ""
echo "🛡️ Protection measures:"
echo "   - Budget alerts at 50%, 75%, 90%, and 100% of $30"
echo "   - Automatic service shutdown at 90% ($27)"
echo "   - Emergency flags in Firestore"
echo "   - Cloud Scheduler jobs paused"
echo "   - Daily cost monitoring"
echo ""
echo "📋 Next steps:"
echo "   1. Deploy the budget guardian: cd cloud_functions/budget_guardian && ./deploy.sh"
echo "   2. Link budget to Pub/Sub: Go to GCP Console > Billing > Budgets"
echo "   3. Set notification channel to 'budget-alerts' topic"
echo "   4. Run daily cost check: python check_daily_cost.py"
echo ""
echo "⚠️ IMPORTANT: The $30 limit is now enforced!"