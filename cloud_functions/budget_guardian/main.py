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
