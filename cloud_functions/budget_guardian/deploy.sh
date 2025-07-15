#!/bin/bash
gcloud functions deploy budget-guardian \
    --runtime python310 \
    --trigger-topic budget-alerts \
    --entry-point budget_alert_handler \
    --memory 256MB \
    --timeout 300s \
    --set-env-vars GCP_PROJECT=$PROJECT_ID
