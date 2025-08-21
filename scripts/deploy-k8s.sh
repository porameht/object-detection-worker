#!/bin/bash
set -e

# Deploy in proper order to avoid namespace issues
echo "Creating namespace first..."
kubectl apply -f k8s/00-namespace.yaml

echo "Waiting for namespace to be ready..."
kubectl wait --for=condition=Ready namespace/object-detection --timeout=60s

echo "Applying remaining resources..."
kubectl apply -f k8s/ --recursive

echo "Checking deployment rollout..."
kubectl rollout status deployment/object-detection-worker -n object-detection

echo "Getting services..."
kubectl get services -n object-detection -o wide