# Athena DeFi Agent - GCP Infrastructure with Terraform

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration for state management
  backend "gcs" {
    bucket = var.terraform_state_bucket
    prefix = "athena-agent/terraform.tfstate"
  }
}

# Configure providers
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Local variables
locals {
  services = [
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "serviceusage.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "firestore.googleapis.com",
    "bigquery.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com"
  ]
  
  agent_name = "athena-defi-agent"
  
  # Cloud Function names
  functions = {
    market_data_collector = "market-data-collector"
    hourly_analysis      = "hourly-analysis"
    daily_summary        = "daily-summary"
  }
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset(local.services)
  
  project = var.project_id
  service = each.value
  
  disable_on_destroy = false
}

# Create service account for the agent
resource "google_service_account" "athena_agent" {
  account_id   = "${local.agent_name}-sa"
  display_name = "Athena DeFi Agent Service Account"
  description  = "Service account for Athena DeFi Agent operations"
  
  depends_on = [google_project_service.apis]
}

# IAM roles for the service account
resource "google_project_iam_member" "athena_agent_roles" {
  for_each = toset([
    "roles/firestore.user",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/secretmanager.secretAccessor",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/cloudfunctions.invoker"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.athena_agent.email}"
}

# Create service account key
resource "google_service_account_key" "athena_agent_key" {
  service_account_id = google_service_account.athena_agent.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Store service account key in Secret Manager
resource "google_secret_manager_secret" "athena_sa_key" {
  secret_id = "athena-agent-sa-key"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "athena_sa_key_version" {
  secret      = google_secret_manager_secret.athena_sa_key.id
  secret_data = base64decode(google_service_account_key.athena_agent_key.private_key)
}

# Firestore database
resource "google_firestore_database" "athena_db" {
  project     = var.project_id
  name        = var.firestore_database_id
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"
  
  depends_on = [google_project_service.apis]
}

# BigQuery dataset
resource "google_bigquery_dataset" "athena_dataset" {
  dataset_id  = var.bigquery_dataset_id
  project     = var.project_id
  location    = var.region
  
  friendly_name   = "Athena DeFi Agent Analytics"
  description     = "Dataset for Athena DeFi Agent analytics and historical data"
  
  default_table_expiration_ms = 31536000000  # 1 year
  
  access {
    role          = "OWNER"
    user_by_email = google_service_account.athena_agent.email
  }
  
  depends_on = [google_project_service.apis]
}

# BigQuery tables
resource "google_bigquery_table" "tables" {
  for_each = {
    market_data = {
      description = "Market data collected from external APIs"
      schema = file("${path.module}/schemas/market_data.json")
    }
    hourly_analysis = {
      description = "Hourly market analysis results"
      schema = file("${path.module}/schemas/hourly_analysis.json")
    }
    daily_summaries = {
      description = "Daily performance summaries"
      schema = file("${path.module}/schemas/daily_summaries.json")
    }
    agent_costs = {
      description = "Agent operational costs tracking"
      schema = file("${path.module}/schemas/agent_costs.json")
    }
    agent_decisions = {
      description = "Agent decision records"
      schema = file("${path.module}/schemas/agent_decisions.json")
    }
    agent_memories = {
      description = "Agent memory formation records"
      schema = file("${path.module}/schemas/agent_memories.json")
    }
  }
  
  dataset_id = google_bigquery_dataset.athena_dataset.dataset_id
  table_id   = each.key
  project    = var.project_id
  
  description = each.value.description
  schema      = each.value.schema
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  
  clustering = ["timestamp"]
}

# Artifact Registry for Cloud Functions
resource "google_artifact_registry_repository" "athena_functions" {
  repository_id = "athena-functions"
  location      = var.region
  format        = "PYTHON"
  
  description = "Repository for Athena DeFi Agent Cloud Functions"
  
  depends_on = [google_project_service.apis]
}

# Cloud Storage bucket for Cloud Functions source
resource "google_storage_bucket" "athena_functions_source" {
  name     = "${var.project_id}-athena-functions-source"
  location = var.region
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Cloud Functions
resource "google_cloudfunctions2_function" "athena_functions" {
  for_each = local.functions
  
  name     = each.value
  location = var.region
  project  = var.project_id
  
  build_config {
    runtime     = "python311"
    entry_point = "${replace(each.key, "_", "-")}_http"
    
    source {
      storage_source {
        bucket = google_storage_bucket.athena_functions_source.name
        object = "${each.key}.zip"
      }
    }
  }
  
  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = each.key == "daily_summary" ? "512Mi" : "256Mi"
    timeout_seconds    = each.key == "daily_summary" ? 540 : 120
    
    environment_variables = {
      GCP_PROJECT_ID      = var.project_id
      FIRESTORE_DATABASE  = var.firestore_database_id
      BIGQUERY_DATASET    = var.bigquery_dataset_id
      ANTHROPIC_API_KEY   = var.anthropic_api_key
      LANGSMITH_API_KEY   = var.langsmith_api_key
      LANGSMITH_PROJECT   = var.langsmith_project
    }
    
    service_account_email = google_service_account.athena_agent.email
  }
  
  depends_on = [
    google_project_service.apis,
    google_bigquery_dataset.athena_dataset,
    google_firestore_database.athena_db
  ]
}

# Cloud Scheduler jobs
resource "google_cloud_scheduler_job" "market_data_collector" {
  name             = "market-data-collection"
  description      = "Collect market data every 15 minutes"
  schedule         = "*/15 * * * *"
  time_zone        = var.scheduler_timezone
  attempt_deadline = "120s"
  
  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions2_function.athena_functions["market_data_collector"].service_config[0].uri
    
    oidc_token {
      service_account_email = google_service_account.athena_agent.email
    }
  }
  
  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "hourly_analysis" {
  name             = "hourly-market-analysis"
  description      = "Perform hourly market analysis"
  schedule         = "0 * * * *"
  time_zone        = var.scheduler_timezone
  attempt_deadline = "300s"
  
  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions2_function.athena_functions["hourly_analysis"].service_config[0].uri
    
    oidc_token {
      service_account_email = google_service_account.athena_agent.email
    }
  }
  
  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "daily_summary" {
  name             = "daily-performance-summary"
  description      = "Generate daily performance summary"
  schedule         = "0 0 * * *"
  time_zone        = var.scheduler_timezone
  attempt_deadline = "540s"
  
  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions2_function.athena_functions["daily_summary"].service_config[0].uri
    
    oidc_token {
      service_account_email = google_service_account.athena_agent.email
    }
  }
  
  depends_on = [google_project_service.apis]
}

# Monitoring alert policy for agent health
resource "google_monitoring_alert_policy" "athena_agent_health" {
  display_name = "Athena Agent Health Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Function Errors"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_function\" AND resource.labels.function_name=~\"athena-.*\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      duration        = "300s"
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  depends_on = [google_project_service.apis]
}

# Log sink for agent logs
resource "google_logging_project_sink" "athena_logs" {
  name        = "athena-agent-logs"
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.athena_dataset.dataset_id}"
  
  filter = "resource.type=\"cloud_function\" AND resource.labels.function_name=~\"athena-.*\""
  
  unique_writer_identity = true
  
  bigquery_options {
    use_partitioned_tables = true
  }
}

# Grant BigQuery Data Editor role to log sink
resource "google_bigquery_dataset_iam_member" "log_sink_writer" {
  dataset_id = google_bigquery_dataset.athena_dataset.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.athena_logs.writer_identity
}