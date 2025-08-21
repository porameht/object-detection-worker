#!/bin/bash

# Build and Push Docker Image Script for GCP
# Usage: ./scripts/build-push.sh [tag]

set -e

IMAGE_TAG=${1:-"latest"}
PROJECT_ID=${GCP_PROJECT_ID:-"processing-469712"}
GAR_LOCATION=${GAR_LOCATION:-"asia-southeast1"}
REPOSITORY_NAME="object-detection-worker"

GAR_REGISTRY="$GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME"

echo "Building and pushing Docker image"
echo "Registry: $GAR_REGISTRY"
echo "Repository: $REPOSITORY_NAME"
echo "Tag: $IMAGE_TAG"

# Login to GAR
echo "Logging in to Google Artifact Registry..."
gcloud auth configure-docker $GAR_LOCATION-docker.pkg.dev

# Build image
echo "Building Docker image..."
docker build -t $REPOSITORY_NAME:$IMAGE_TAG .

# Tag for GAR
echo "Tagging image for GAR..."
docker tag $REPOSITORY_NAME:$IMAGE_TAG $GAR_REGISTRY/$REPOSITORY_NAME:$IMAGE_TAG

# Also tag as latest if not already latest
if [ "$IMAGE_TAG" != "latest" ]; then
    docker tag $REPOSITORY_NAME:$IMAGE_TAG $GAR_REGISTRY/$REPOSITORY_NAME:latest
fi

# Push to GAR
echo "Pushing image to GAR..."
docker push $GAR_REGISTRY/$REPOSITORY_NAME:$IMAGE_TAG

if [ "$IMAGE_TAG" != "latest" ]; then
    docker push $GAR_REGISTRY/$REPOSITORY_NAME:latest
fi

echo "Image pushed successfully!"
echo "Image URI: $GAR_REGISTRY/$REPOSITORY_NAME:$IMAGE_TAG"