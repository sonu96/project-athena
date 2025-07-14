# Terraform outputs for Athena DeFi Agent infrastructure

output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "The GCP region"
  value       = var.region
}

output "service_account_email" {
  description = "Service account email for the Athena agent"
  value       = google_service_account.athena_agent.email
}

output "service_account_key_secret" {
  description = "Secret Manager secret containing service account key"
  value       = google_secret_manager_secret.athena_sa_key.secret_id
  sensitive   = true
}

output "firestore_database" {
  description = "Firestore database information"
  value = {
    name     = google_firestore_database.athena_db.name
    location = google_firestore_database.athena_db.location_id
  }
}

output "bigquery_dataset" {
  description = "BigQuery dataset information"
  value = {
    dataset_id = google_bigquery_dataset.athena_dataset.dataset_id
    location   = google_bigquery_dataset.athena_dataset.location
    tables     = keys(google_bigquery_table.tables)
  }
}

output "cloud_functions" {
  description = "Cloud Functions information"
  value = {
    for k, v in google_cloudfunctions2_function.athena_functions : k => {
      name = v.name
      uri  = v.service_config[0].uri
    }
  }
}

output "scheduler_jobs" {
  description = "Cloud Scheduler jobs"
  value = {
    market_data_collector = google_cloud_scheduler_job.market_data_collector.name
    hourly_analysis      = google_cloud_scheduler_job.hourly_analysis.name
    daily_summary        = google_cloud_scheduler_job.daily_summary.name
  }
}

output "storage_bucket" {
  description = "Cloud Functions source storage bucket"
  value = {
    name = google_storage_bucket.athena_functions_source.name
    url  = google_storage_bucket.athena_functions_source.url
  }
}

output "artifact_registry" {
  description = "Artifact Registry repository"
  value = {
    name     = google_artifact_registry_repository.athena_functions.name
    location = google_artifact_registry_repository.athena_functions.location
  }
}

output "monitoring_alert_policy" {
  description = "Monitoring alert policy"
  value = {
    name         = google_monitoring_alert_policy.athena_agent_health.name
    display_name = google_monitoring_alert_policy.athena_agent_health.display_name
  }
}

output "log_sink" {
  description = "Log sink information"
  value = {
    name        = google_logging_project_sink.athena_logs.name
    destination = google_logging_project_sink.athena_logs.destination
  }
}

output "deployment_commands" {
  description = "Commands for deploying the agent"
  value = {
    gcloud_auth = "gcloud auth activate-service-account --key-file=<path-to-key>"
    
    deploy_functions = "cd cloud_functions && ./deploy.sh"
    
    docker_build = "docker build -t gcr.io/${var.project_id}/athena-agent:latest ."
    
    docker_push = "docker push gcr.io/${var.project_id}/athena-agent:latest"
    
    cloud_run_deploy = "gcloud run deploy athena-agent --image gcr.io/${var.project_id}/athena-agent:latest --region ${var.region} --service-account ${google_service_account.athena_agent.email}"
  }
}

output "environment_variables" {
  description = "Environment variables for the agent"
  value = {
    GCP_PROJECT_ID     = var.project_id
    FIRESTORE_DATABASE = var.firestore_database_id
    BIGQUERY_DATASET   = var.bigquery_dataset_id
    LANGSMITH_PROJECT  = var.langsmith_project
  }
  sensitive = false
}

output "secret_environment_variables" {
  description = "Secret environment variables to be set manually"
  value = {
    ANTHROPIC_API_KEY                 = "Set in Secret Manager or environment"
    LANGSMITH_API_KEY                 = "Set in Secret Manager or environment"
    MEM0_API_KEY                      = "Set in Secret Manager or environment"
    CDP_API_KEY_NAME                  = "Set in Secret Manager or environment"
    CDP_API_KEY_SECRET                = "Set in Secret Manager or environment"
    GOOGLE_APPLICATION_CREDENTIALS    = "/path/to/service-account-key.json"
  }
  sensitive = true
}

output "useful_commands" {
  description = "Useful commands for managing the infrastructure"
  value = {
    # Terraform commands
    terraform_plan    = "terraform plan -var-file=terraform.tfvars"
    terraform_apply   = "terraform apply -var-file=terraform.tfvars"
    terraform_destroy = "terraform destroy -var-file=terraform.tfvars"
    
    # GCP commands
    view_functions    = "gcloud functions list --filter='name:athena'"
    view_logs        = "gcloud logging read 'resource.type=\"cloud_function\" AND resource.labels.function_name=~\"athena-.*\"' --limit=50"
    view_metrics     = "gcloud monitoring metrics list --filter='display_name:athena'"
    
    # BigQuery commands
    query_market_data = "bq query --use_legacy_sql=false 'SELECT * FROM `${var.project_id}.${var.bigquery_dataset_id}.market_data` ORDER BY timestamp DESC LIMIT 10'"
    query_costs      = "bq query --use_legacy_sql=false 'SELECT * FROM `${var.project_id}.${var.bigquery_dataset_id}.agent_costs` ORDER BY timestamp DESC LIMIT 10'"
    
    # Firestore commands
    view_collections = "gcloud firestore collections list --database=${var.firestore_database_id}"
  }
}

output "monitoring_urls" {
  description = "URLs for monitoring the agent"
  value = {
    cloud_console     = "https://console.cloud.google.com/home/dashboard?project=${var.project_id}"
    cloud_functions   = "https://console.cloud.google.com/functions/list?project=${var.project_id}"
    cloud_scheduler   = "https://console.cloud.google.com/cloudscheduler?project=${var.project_id}"
    bigquery         = "https://console.cloud.google.com/bigquery?project=${var.project_id}&d=${var.bigquery_dataset_id}"
    firestore        = "https://console.cloud.google.com/firestore/data?project=${var.project_id}"
    monitoring       = "https://console.cloud.google.com/monitoring?project=${var.project_id}"
    logging          = "https://console.cloud.google.com/logs/query?project=${var.project_id}"
  }
}