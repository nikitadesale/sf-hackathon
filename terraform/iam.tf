# ═══════════════════════════════════════════════════════════════════════════════
# Service Account: ShadowAgentMap Scanner
# Role: scans GCP resources + writes to BigQuery
# Used by: the main backend / Cloud Run scanner service
# ═══════════════════════════════════════════════════════════════════════════════

resource "google_service_account" "scanner" {
  account_id   = "shadowagentmap-sa"
  display_name = "ShadowAgentMap Scanner"
  description  = "Runs the AI agent discovery scanner. Read-only on GCP resources, write to BigQuery."
  project      = var.project_id
}

# List Cloud Run services (discovery)
resource "google_project_iam_member" "scanner_run_viewer" {
  project = var.project_id
  role    = "roles/run.viewer"
  member  = "serviceAccount:${google_service_account.scanner.email}"
}

# List Vertex AI endpoints (discovery)
resource "google_project_iam_member" "scanner_vertex_viewer" {
  project = var.project_id
  role    = "roles/aiplatform.viewer"
  member  = "serviceAccount:${google_service_account.scanner.email}"
}

# Write discovered agents to BigQuery
resource "google_project_iam_member" "scanner_bq_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.scanner.email}"
}

# Run BigQuery jobs (SELECT, INSERT, TRUNCATE)
resource "google_project_iam_member" "scanner_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.scanner.email}"
}

# Write application logs
resource "google_project_iam_member" "scanner_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.scanner.email}"
}


# ═══════════════════════════════════════════════════════════════════════════════
# Service Account: Trusted HR Processor (authorized demo agent)
# Role: logging only — strictly minimal, by design
# Used by: trusted-hr-processor Cloud Run service
# ═══════════════════════════════════════════════════════════════════════════════

resource "google_service_account" "trusted_hr" {
  account_id   = "trusted-hr-agent-sa"
  display_name = "Trusted HR Processor Agent"
  description  = "Minimal-permission SA for the authorized demo agent. Logging only."
  project      = var.project_id
}

# Only logs — nothing else
resource "google_project_iam_member" "trusted_hr_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.trusted_hr.email}"
}
