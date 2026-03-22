variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "waybackhome-rw9xuoxqhoap3wax3s"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "bq_dataset" {
  description = "BigQuery dataset name"
  type        = string
  default     = "shadow_agent_map"
}

variable "bq_table" {
  description = "BigQuery table name"
  type        = string
  default     = "agent_registry"
}
