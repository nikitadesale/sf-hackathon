output "scanner_sa_email" {
  description = "Service account for the ShadowAgentMap scanner backend"
  value       = google_service_account.scanner.email
}

output "trusted_hr_sa_email" {
  description = "Service account for the trusted-hr-processor demo agent"
  value       = google_service_account.trusted_hr.email
}

output "bq_table_full_id" {
  description = "Fully-qualified BigQuery table ID"
  value       = "${var.project_id}.${var.bq_dataset}.${var.bq_table}"
}
