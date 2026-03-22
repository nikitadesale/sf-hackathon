#!/bin/bash
set -e

PROJECT_ID="waybackhome-rw9xuoxqhoap3wax3s"
REGION="us-central1"
DATASET="shadow_agent_map"

echo "==> Setting GCP project..."
gcloud config set project $PROJECT_ID

echo "==> Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com

echo "==> Creating BigQuery dataset..."
bq --location=US mk --dataset ${PROJECT_ID}:${DATASET} 2>/dev/null || echo "Dataset already exists, skipping."

echo "==> Creating agent_registry table..."
bq mk --table \
  ${PROJECT_ID}:${DATASET}.agent_registry \
  agent_id:STRING,name:STRING,endpoint:STRING,deployed_by:STRING,source:STRING,ingress:STRING,risk_score:FLOAT,status:STRING,risk_reasons:STRING,last_seen:TIMESTAMP \
  2>/dev/null || echo "Table already exists, skipping."

echo ""
echo "Setup complete. Project: $PROJECT_ID | Region: $REGION"
