# ── BigQuery dataset ──────────────────────────────────────────────────────────

resource "google_bigquery_dataset" "shadow_agent_map" {
  dataset_id    = var.bq_dataset
  friendly_name = "Shadow Agent Map"
  description   = "Registry of discovered AI agents, their risk scores, and audit trail."
  location      = "US"
  project       = var.project_id

  depends_on = [google_project_service.apis]

  lifecycle {
    prevent_destroy = false
    ignore_changes  = [labels]
  }
}

# ── agent_registry table ──────────────────────────────────────────────────────

resource "google_bigquery_table" "agent_registry" {
  dataset_id          = google_bigquery_dataset.shadow_agent_map.dataset_id
  table_id            = var.bq_table
  project             = var.project_id
  deletion_protection = false

  schema = jsonencode([
    { name = "agent_id",     type = "STRING",    mode = "REQUIRED", description = "Unique identifier (Cloud Run UID or Vertex endpoint ID)" },
    { name = "name",         type = "STRING",    mode = "REQUIRED", description = "Service / endpoint name" },
    { name = "endpoint",     type = "STRING",    mode = "NULLABLE", description = "Public or internal URL" },
    { name = "deployed_by",  type = "STRING",    mode = "NULLABLE", description = "Service account email" },
    { name = "source",       type = "STRING",    mode = "REQUIRED", description = "cloud_run | vertex_ai" },
    { name = "ingress",      type = "STRING",    mode = "REQUIRED", description = "public | internal" },
    { name = "risk_score",   type = "FLOAT",     mode = "REQUIRED", description = "0–100 risk score" },
    { name = "status",       type = "STRING",    mode = "REQUIRED", description = "approved | shadow | compromised" },
    { name = "risk_reasons", type = "STRING",    mode = "NULLABLE", description = "Pipe-separated risk factors" },
    { name = "last_seen",    type = "TIMESTAMP", mode = "NULLABLE", description = "Last scan timestamp" },
  ])

  lifecycle {
    ignore_changes = [schema]
  }
}
