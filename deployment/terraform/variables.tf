# Terraform variables for Athena DeFi Agent GCP infrastructure

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for resources"
  type        = string
  default     = "us-central1-a"
}

variable "terraform_state_bucket" {
  description = "GCS bucket for Terraform state"
  type        = string
}

variable "firestore_database_id" {
  description = "Firestore database ID"
  type        = string
  default     = "athena-agent"
}

variable "firestore_location" {
  description = "Firestore database location"
  type        = string
  default     = "us-central"
}

variable "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
  default     = "athena_defi_agent"
}

variable "scheduler_timezone" {
  description = "Timezone for Cloud Scheduler jobs"
  type        = string
  default     = "UTC"
}

variable "anthropic_api_key" {
  description = "Anthropic API key for LLM operations"
  type        = string
  sensitive   = true
}

variable "langsmith_api_key" {
  description = "LangSmith API key for workflow monitoring"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langsmith_project" {
  description = "LangSmith project name"
  type        = string
  default     = "athena-defi-agent"
}

variable "notification_channels" {
  description = "List of notification channels for alerts"
  type        = list(string)
  default     = []
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "agent_config" {
  description = "Agent configuration parameters"
  type = object({
    starting_treasury     = number
    max_daily_cost       = number
    observation_interval = number
    emergency_threshold  = number
  })
  
  default = {
    starting_treasury     = 100.0
    max_daily_cost       = 10.0
    observation_interval = 3600    # 1 hour
    emergency_threshold  = 25.0
  }
}

variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable structured logging"
  type        = bool
  default     = true
}

variable "function_memory" {
  description = "Memory allocation for Cloud Functions"
  type = map(string)
  
  default = {
    market_data_collector = "256Mi"
    hourly_analysis      = "256Mi"
    daily_summary        = "512Mi"
  }
}

variable "function_timeout" {
  description = "Timeout for Cloud Functions (seconds)"
  type = map(number)
  
  default = {
    market_data_collector = 60
    hourly_analysis      = 120
    daily_summary        = 300
  }
}

variable "bigquery_table_expiration_days" {
  description = "Default table expiration in days"
  type        = number
  default     = 365
}

variable "cloud_functions_max_instances" {
  description = "Maximum instances for Cloud Functions"
  type        = number
  default     = 10
}

variable "enable_vpc_connector" {
  description = "Enable VPC connector for Cloud Functions"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  
  default = {
    project     = "athena-defi-agent"
    environment = "production"
    managed_by  = "terraform"
  }
}