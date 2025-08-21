#!/bin/bash

# GCP GKE Setup Script for Object Detection Worker
# Usage: ./scripts/setup-gcp.sh [cluster-name] [zone]

set -e

CLUSTER_NAME=${1:-"object-detection-cluster"}
GCP_ZONE=${2:-"asia-southeast1-a"}
PROJECT_ID="processing-469712"
REPOSITORY_NAME="object-detection-worker"
GAR_LOCATION="asia-southeast1"

echo "Setting up GCP infrastructure for Object Detection Worker"
echo "Cluster: $CLUSTER_NAME"
echo "Zone: $GCP_ZONE"
echo "Project: $PROJECT_ID"
echo "Repository: $REPOSITORY_NAME"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo "Checking required tools..."
if ! command_exists gcloud; then
    echo "Error: gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command_exists kubectl; then
    echo "Error: kubectl is not installed"
    echo "Install from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Create Artifact Registry repository
echo "Creating Artifact Registry repository..."
gcloud artifacts repositories describe $REPOSITORY_NAME \
    --location=$GAR_LOCATION >/dev/null 2>&1 || {
    echo "Creating GAR repository: $REPOSITORY_NAME"
    gcloud artifacts repositories create $REPOSITORY_NAME \
        --repository-format=docker \
        --location=$GAR_LOCATION \
        --description="Object Detection Worker Docker images"
}

# Check if GKE cluster exists
echo "Checking GKE cluster..."
if gcloud container clusters describe $CLUSTER_NAME --zone=$GCP_ZONE >/dev/null 2>&1; then
    echo "GKE cluster $CLUSTER_NAME already exists"
else
    echo "Creating GKE cluster: $CLUSTER_NAME"
    read -p "This will take 10-15 minutes. Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud container clusters create $CLUSTER_NAME \
            --zone=$GCP_ZONE \
            --num-nodes=2 \
            --machine-type=e2-medium \
            --enable-autoscaling \
            --min-nodes=1 \
            --max-nodes=3 \
            --enable-autorepair \
            --enable-autoupgrade
    else
        echo "Skipping cluster creation"
    fi
fi

# Update kubeconfig
echo "Updating kubeconfig..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$GCP_ZONE

# Create namespace
echo "Creating namespace..."
kubectl apply -f k8s/namespace.yml || true

# Apply service account
echo "Applying service account..."
kubectl apply -f k8s/serviceaccount.yml || true

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update k8s/configmap.yaml with your GCP project details"
echo "2. Update k8s/configmap.yml with your configuration (already done)"
echo "3. Set up GitHub secrets using ./setup-gke-credentials.sh"
echo "4. Push to main branch to trigger deployment"
echo ""
echo "GAR Repository URI: $GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/$REPOSITORY_NAME"