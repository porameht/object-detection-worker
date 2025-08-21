#!/bin/bash

# GKE Deployment Setup Script
# This script prepares all necessary GCP resources for GitHub Actions deployment

set -e

# Configuration
PROJECT_ID="processing-469712"  # Project ID ของคุณ
SERVICE_ACCOUNT_NAME="github-actions-deployer"
GAR_LOCATION="asia-southeast1"
GAR_REPOSITORY="object-detection-worker"
GKE_CLUSTER_NAME="object-detection-cluster"
GKE_ZONE="asia-southeast1-a"
GITHUB_REPO="porameht/object-detection-worker"  # แทนที่ด้วย GitHub repo ของคุณ

echo "🚀 Starting GKE deployment setup..."

# 1. Create service account
echo "📦 Creating service account..."
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
    --display-name="GitHub Actions Deployer" \
    --project=${PROJECT_ID} || echo "Service account might already exist"

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# 2. Grant necessary permissions
echo "🔐 Granting permissions..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/container.developer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/storage.admin"

# 3. Create Artifact Registry repository
echo "📚 Creating Artifact Registry repository..."
gcloud artifacts repositories create ${GAR_REPOSITORY} \
    --repository-format=docker \
    --location=${GAR_LOCATION} \
    --description="Object Detection worker Docker images" \
    --project=${PROJECT_ID} || echo "Repository might already exist"

# 4. Create GKE cluster (if not exists)
echo "☸️ Creating GKE cluster..."
gcloud container clusters create ${GKE_CLUSTER_NAME} \
    --zone=${GKE_ZONE} \
    --num-nodes=2 \
    --machine-type=e2-medium \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=3 \
    --project=${PROJECT_ID} || echo "Cluster might already exist"

# 5. Set up Workload Identity Federation
echo "🔗 Setting up Workload Identity Federation..."

# Create Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
    --location="global" \
    --display-name="GitHub Actions Pool" \
    --project=${PROJECT_ID} || echo "Pool might already exist"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --project=${PROJECT_ID} || echo "Provider might already exist"

# Grant service account impersonation
gcloud iam service-accounts add-iam-policy-binding ${SERVICE_ACCOUNT_EMAIL} \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/$(gcloud config get-value project --quiet)/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}" \
    --project=${PROJECT_ID}

# Get Workload Identity Provider resource name
WIF_PROVIDER=$(gcloud iam workload-identity-pools providers describe github-provider \
    --workload-identity-pool=github-pool \
    --location=global \
    --format="value(name)" \
    --project=${PROJECT_ID})

echo "✅ Setup complete!"
echo ""
echo "========================================="
echo "GitHub Actions Secrets Configuration"
echo "========================================="
echo ""
echo "Add these secrets to your GitHub repository:"
echo "(Settings → Secrets and variables → Actions)"
echo ""
echo "GCP_PROJECT_ID=${PROJECT_ID}"
echo "WIF_PROVIDER=${WIF_PROVIDER}"
echo "WIF_SERVICE_ACCOUNT=${SERVICE_ACCOUNT_EMAIL}"
echo ""
echo "========================================="