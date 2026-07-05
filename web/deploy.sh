#!/usr/bin/env bash
set -euo pipefail

# Postmeet — Cloud Run deploy script
# Usage:
#   ./deploy.sh YOUR_PROJECT_ID YOUR_NVIDIA_API_KEY
#
# Prereqs (one-time):
#   gcloud auth login
#   gcloud config set project YOUR_PROJECT_ID

PROJECT_ID="${1:?Usage: ./deploy.sh PROJECT_ID NVIDIA_API_KEY}"
API_KEY="${2:?Usage: ./deploy.sh PROJECT_ID NVIDIA_API_KEY}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-postmeet}"
SECRET_NAME="${SECRET_NAME:-nvidia-api-key}"

echo "==> Setting project: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

echo "==> Enabling required APIs (Cloud Run, Cloud Build, Secret Manager)"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com

echo "==> Creating/updating Secret Manager secret: $SECRET_NAME"
if gcloud secrets describe "$SECRET_NAME" >/dev/null 2>&1; then
  echo -n "$API_KEY" | gcloud secrets versions add "$SECRET_NAME" --data-file=-
else
  echo -n "$API_KEY" | gcloud secrets create "$SECRET_NAME" --data-file=- --replication-policy=automatic
fi

echo "==> Granting Cloud Run runtime SA access to the secret"
PROJECT_NUM=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --member="serviceAccount:${PROJECT_NUM}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet

echo "==> Deploying $SERVICE to Cloud Run ($REGION)"
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-secrets "NVIDIA_API_KEY=${SECRET_NAME}:latest" \
  --memory 512Mi \
  --min-instances 1 \
  --max-instances 3 \
  --cpu-boost \
  --timeout 60 \
  --quiet

URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')
echo
echo "✅ Deployed: $URL"
echo "   Smoke test: curl -s $URL/ | head -5"
