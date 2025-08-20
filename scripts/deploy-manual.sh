#!/bin/bash

# Manual Deployment Script
# Usage: ./scripts/deploy-manual.sh [image-tag]

set -e

IMAGE_TAG=${1:-"latest"}
AWS_REGION=${AWS_REGION:-"us-east-1"}
CLUSTER_NAME=${CLUSTER_NAME:-"object-detection-cluster"}

echo "Manual deployment to EKS"
echo "Image tag: $IMAGE_TAG"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $AWS_REGION"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="object-detection-worker"
ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
IMAGE_URI="$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"

# Update kubeconfig
echo "Updating kubeconfig..."
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

# Create a temporary deployment file with the correct image
echo "Preparing deployment with image: $IMAGE_URI"
cp k8s/deployment.yml /tmp/deployment-temp.yml
sed -i.bak "s|IMAGE_PLACEHOLDER|$IMAGE_URI|g" /tmp/deployment-temp.yml

# Apply all manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/secret.yml
kubectl apply -f k8s/serviceaccount.yml
kubectl apply -f /tmp/deployment-temp.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/hpa.yml
kubectl apply -f k8s/networkpolicy.yml

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/object-detection-worker -n object-detection --timeout=300s

# Show status
echo "Deployment status:"
kubectl get pods -n object-detection -l app=object-detection-worker
kubectl get svc -n object-detection
kubectl get hpa -n object-detection

# Cleanup
rm -f /tmp/deployment-temp.yml /tmp/deployment-temp.yml.bak

echo "Manual deployment completed successfully!"