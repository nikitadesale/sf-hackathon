#!/bin/bash
# Deploys the ShadowAgentMap backend to Cloud Run using the Terraform-created SA.
# Run `terraform apply` in ../terraform/ first.
set -e

PROJECT_ID="waybackhome-rw9xuoxqhoap3wax3s"
REGION="us-central1"
SA_EMAIL="shadowagentmap-sa@${PROJECT_ID}.iam.gserviceaccount.com"
SERVICE_NAME="shadow-agent-map"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "==> Building image (frontend + backend)..."
cd "$(dirname "$0")/.."
gcloud builds submit --tag ${IMAGE} --project=${PROJECT_ID}

echo "==> Deploying ShadowAgentMap backend to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --service-account=${SA_EMAIL} \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=True,BQ_DATASET=shadow_agent_map,BQ_TABLE=agent_registry" \
  --set-secrets="GOOGLE_API_KEY=gemini-api-key:latest" \
  --max-instances=2 \
  --memory=512Mi \
  --cpu=1

echo ""
echo "✓ ShadowAgentMap deployed!"
echo "  Service account: ${SA_EMAIL}"
echo "  Permissions: Cloud Run viewer, Vertex AI viewer, BigQuery editor"
gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} \
  --format="value(status.url)"
