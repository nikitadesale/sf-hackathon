#!/bin/bash
# Deploys the 3 demo agents that make the ShadowAgentMap demo story clear.
#
# After scanning, you will see:
#   trusted-hr-processor  → AUTHORIZED   (approved + private access)
#   invoice-agent-v2      → COMPROMISED  (approved + public = misconfigured)
#   shadow-data-collector → SHADOW       (never approved by IT)
#
# location-analyzer is a real Cloud Run service — scanned as-is.
#
# Run terraform apply in ../terraform/ first to create service accounts.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ID="waybackhome-rw9xuoxqhoap3wax3s"
REGION="us-central1"
SCANNER_SA="shadowagentmap-sa@${PROJECT_ID}.iam.gserviceaccount.com"
HR_SA="trusted-hr-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "======================================================"
echo " Deploying ShadowAgentMap demo agents"
echo " Project: $PROJECT_ID | Region: $REGION"
echo "======================================================"
echo ""

# ── 1. trusted-hr-processor ────────────────────────────────────────────────
# IT-approved, private (no public access), limited service account.
# Will scan as: AUTHORIZED
echo "[1/3] trusted-hr-processor (AUTHORIZED demo)..."
cd "${SCRIPT_DIR}/trusted-hr-processor"
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/trusted-hr-processor" --project=${PROJECT_ID} --quiet
gcloud run deploy trusted-hr-processor \
  --image="gcr.io/${PROJECT_ID}/trusted-hr-processor" \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --service-account=${HR_SA} \
  --no-allow-unauthenticated \
  --ingress=internal \
  --max-instances=1 \
  --memory=256Mi \
  --quiet
echo "  ✓ AUTHORIZED — private, limited SA"

# ── 2. invoice-agent-v2 ────────────────────────────────────────────────────
# IT-approved but deployed publicly by mistake — classic misconfiguration.
# Will scan as: COMPROMISED
echo ""
echo "[2/3] invoice-agent-v2 (COMPROMISED demo)..."
cd "${SCRIPT_DIR}/invoice-agent-v2"
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/invoice-agent-v2" --project=${PROJECT_ID} --quiet
gcloud run deploy invoice-agent-v2 \
  --image="gcr.io/${PROJECT_ID}/invoice-agent-v2" \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --service-account=${SCANNER_SA} \
  --allow-unauthenticated \
  --max-instances=1 \
  --memory=256Mi \
  --quiet
echo "  ✓ COMPROMISED — approved but public (no auth)"

# ── 3. shadow-data-collector ───────────────────────────────────────────────
# Never approved by IT — just appeared. Public access.
# Will scan as: SHADOW
echo ""
echo "[3/3] shadow-data-collector (SHADOW demo)..."
cd "${SCRIPT_DIR}/shadow-data-collector"
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/shadow-data-collector" --project=${PROJECT_ID} --quiet
gcloud run deploy shadow-data-collector \
  --image="gcr.io/${PROJECT_ID}/shadow-data-collector" \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated \
  --max-instances=1 \
  --memory=256Mi \
  --quiet
echo "  ✓ SHADOW — not in IT registry, public access"

# ── Clean up old confusing services ───────────────────────────────────────
echo ""
echo "Cleaning up old demo services..."
for svc in authorized-reporter legit-invoice-processor compromised-reporter; do
  gcloud run services delete $svc --region=${REGION} --project=${PROJECT_ID} --quiet 2>/dev/null \
    && echo "  deleted: $svc" || echo "  skipped: $svc (not found)"
done

echo ""
echo "======================================================"
echo " Done! Run 'Scan Now' in ShadowAgentMap."
echo " Expected results:"
echo "   AUTHORIZED  : trusted-hr-processor"
echo "   COMPROMISED : invoice-agent-v2"
echo "   SHADOW      : shadow-data-collector, location-analyzer"
echo "======================================================"
