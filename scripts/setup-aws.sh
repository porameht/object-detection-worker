#!/bin/bash

# AWS EKS Setup Script
# Usage: ./scripts/setup-aws.sh [cluster-name] [region]

set -e

CLUSTER_NAME=${1:-"object-detection-cluster"}
AWS_REGION=${2:-"us-east-1"}
REPOSITORY_NAME="object-detection-worker"

echo "Setting up AWS infrastructure for Object Detection Worker"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $AWS_REGION"
echo "Repository: $REPOSITORY_NAME"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo "Checking required tools..."
if ! command_exists aws; then
    echo "Error: AWS CLI is not installed"
    exit 1
fi

if ! command_exists eksctl; then
    echo "Error: eksctl is not installed"
    echo "Install from: https://eksctl.io/installation/"
    exit 1
fi

if ! command_exists kubectl; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $ACCOUNT_ID"

# Create ECR repository
echo "Creating ECR repository..."
aws ecr describe-repositories --repository-names $REPOSITORY_NAME --region $AWS_REGION >/dev/null 2>&1 || {
    echo "Creating ECR repository: $REPOSITORY_NAME"
    aws ecr create-repository \
        --repository-name $REPOSITORY_NAME \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true
}

# Check if EKS cluster exists
if eksctl get cluster --name $CLUSTER_NAME --region $AWS_REGION >/dev/null 2>&1; then
    echo "EKS cluster $CLUSTER_NAME already exists"
else
    echo "Creating EKS cluster: $CLUSTER_NAME"
    read -p "This will take 15-20 minutes. Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        eksctl create cluster \
            --name $CLUSTER_NAME \
            --region $AWS_REGION \
            --node-type t3.medium \
            --nodes 3 \
            --nodes-min 2 \
            --nodes-max 10 \
            --managed \
            --with-oidc
    else
        echo "Skipping cluster creation"
    fi
fi

# Update kubeconfig
echo "Updating kubeconfig..."
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

# Create OIDC provider (if not exists)
echo "Setting up OIDC provider..."
eksctl utils associate-iam-oidc-provider \
    --cluster $CLUSTER_NAME \
    --region $AWS_REGION \
    --approve || true

# Create IAM role for service account
echo "Creating IAM role for service account..."
eksctl create iamserviceaccount \
    --name object-detection-worker \
    --namespace object-detection \
    --cluster $CLUSTER_NAME \
    --region $AWS_REGION \
    --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
    --approve \
    --override-existing-serviceaccounts || true

# Update serviceaccount.yml with correct role ARN
ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/eksctl-$CLUSTER_NAME-addon-iamserviceaccount-obj-Role1-*"
echo "Updating serviceaccount.yml with role ARN pattern: $ROLE_ARN"

# Create namespace
echo "Creating namespace..."
kubectl apply -f k8s/namespace.yml || true

# Apply RBAC
echo "Applying RBAC..."
kubectl apply -f k8s/serviceaccount.yml || true

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update k8s/secret.yml with your Redis URL"
echo "2. Update k8s/configmap.yml with your configuration"
echo "3. Set up GitHub secrets:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "4. Push to main branch to trigger deployment"
echo ""
echo "ECR Repository URI: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME"