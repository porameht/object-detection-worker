#!/bin/bash

# Build and Push Docker Image Script
# Usage: ./scripts/build-push.sh [tag]

set -e

IMAGE_TAG=${1:-"latest"}
AWS_REGION=${AWS_REGION:-"us-east-1"}
REPOSITORY_NAME="object-detection-worker"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "Building and pushing Docker image"
echo "Registry: $ECR_REGISTRY"
echo "Repository: $REPOSITORY_NAME"
echo "Tag: $IMAGE_TAG"

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build image
echo "Building Docker image..."
docker build -t $REPOSITORY_NAME:$IMAGE_TAG .

# Tag for ECR
echo "Tagging image for ECR..."
docker tag $REPOSITORY_NAME:$IMAGE_TAG $ECR_REGISTRY/$REPOSITORY_NAME:$IMAGE_TAG

# Also tag as latest if not already latest
if [ "$IMAGE_TAG" != "latest" ]; then
    docker tag $REPOSITORY_NAME:$IMAGE_TAG $ECR_REGISTRY/$REPOSITORY_NAME:latest
fi

# Push to ECR
echo "Pushing image to ECR..."
docker push $ECR_REGISTRY/$REPOSITORY_NAME:$IMAGE_TAG

if [ "$IMAGE_TAG" != "latest" ]; then
    docker push $ECR_REGISTRY/$REPOSITORY_NAME:latest
fi

echo "Image pushed successfully!"
echo "Image URI: $ECR_REGISTRY/$REPOSITORY_NAME:$IMAGE_TAG"