#!/bin/bash

echo "=== Manual Node Pool Scaling ==="

CLUSTER_NAME="object-detection-cluster"
ZONE="asia-southeast1-a"
NODE_POOL="default-pool"

# Check current node pool size
echo "Current node pool size:"
gcloud container node-pools describe $NODE_POOL \
  --cluster=$CLUSTER_NAME \
  --zone=$ZONE \
  --format="value(initialNodeCount)"

# Scale up node pool
NEW_SIZE=${1:-3}  # Default to 3 nodes if not specified
echo "Scaling node pool to $NEW_SIZE nodes..."

gcloud container clusters resize $CLUSTER_NAME \
  --zone=$ZONE \
  --node-pool=$NODE_POOL \
  --num-nodes=$NEW_SIZE \
  --quiet

echo "Node pool scaling initiated. Checking status..."

# Wait for nodes to be ready
echo "Waiting for nodes to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Show updated node status
echo -e "\nUpdated node status:"
kubectl get nodes

echo "Scaling completed!"