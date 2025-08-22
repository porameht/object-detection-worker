#!/bin/bash

set -e

PROJECT_ID="processing-469712"
SERVICE_ACCOUNT_NAME="object-detection-worker"
KEY_FILE="service-account-key.json"

echo "=== Setting up GCP Authentication for Worker ==="

# Create service account
echo "Creating service account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --display-name="Object Detection Worker Service Account" \
  --project=$PROJECT_ID || echo "Service account already exists"

# Grant necessary permissions
echo "Granting permissions..."
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Pub/Sub permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/pubsub.subscriber"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/pubsub.publisher"

# Storage permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectCreator"

# Create service account key
echo "Creating service account key..."
gcloud iam service-accounts keys create $KEY_FILE \
  --iam-account="${SERVICE_ACCOUNT_EMAIL}" \
  --project=$PROJECT_ID

# Create Kubernetes secret
echo "Creating Kubernetes secret..."
kubectl create secret generic gcp-service-account-key \
  --from-file=key.json=$KEY_FILE \
  --dry-run=client -o yaml | kubectl apply -f -

# Clean up local key file
rm -f $KEY_FILE

echo "=== Setup Complete ==="
echo "Service Account: ${SERVICE_ACCOUNT_EMAIL}"
echo "Kubernetes Secret: gcp-service-account-key"

# Verify Pub/Sub subscription exists
echo -e "\nVerifying Pub/Sub subscription..."
gcloud pubsub subscriptions describe detection-workers \
  --project=$PROJECT_ID || {
    echo "Creating subscription..."
    gcloud pubsub subscriptions create detection-workers \
      --topic=object-detection-tasks \
      --project=$PROJECT_ID \
      --ack-deadline=60 \
      --max-delivery-attempts=5
  }

echo -e "\nAuthentication setup completed!"