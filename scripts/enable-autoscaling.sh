#!/bin/bash

echo "=== Enabling GKE Cluster Autoscaling ==="

CLUSTER_NAME="object-detection-cluster"
ZONE="asia-southeast1-a"
NODE_POOL="default-pool"

# Enable cluster autoscaler
echo "Enabling cluster autoscaler for node pool: $NODE_POOL"
gcloud container clusters update $CLUSTER_NAME \
  --zone=$ZONE \
  --enable-autoscaling \
  --node-pool=$NODE_POOL \
  --min-nodes=1 \
  --max-nodes=5

# Enable node auto-provisioning (NAP)
echo "Enabling Node Auto-Provisioning (NAP)..."
gcloud container clusters update $CLUSTER_NAME \
  --zone=$ZONE \
  --enable-autoprovisioning \
  --min-cpu=1 \
  --max-cpu=16 \
  --min-memory=1 \
  --max-memory=64 \
  --max-surge-upgrade=1 \
  --max-unavailable-upgrade=0

echo "Autoscaling configuration completed!"

# Show current autoscaling status
echo -e "\nCurrent autoscaling status:"
gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE | grep -A 10 "autoscaling"