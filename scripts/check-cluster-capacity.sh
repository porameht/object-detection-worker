#!/bin/bash

echo "=== Checking GKE Cluster Capacity ==="

# Check current node pool status
echo "Current node pools:"
gcloud container node-pools list --cluster=object-detection-cluster --zone=asia-southeast1-a

# Check node status
echo -e "\nNode status:"
kubectl get nodes -o wide

# Check resource capacity and usage
echo -e "\nNode resource usage:"
kubectl top nodes

# Check pod resource requests
echo -e "\nPod resource requests:"
kubectl describe nodes | grep -A 6 "Allocated resources"

# Check pending pods
echo -e "\nPending pods:"
kubectl get pods --field-selector=status.phase=Pending

# Check pod events for scheduling issues
echo -e "\nRecent pod events:"
kubectl get events --sort-by=.metadata.creationTimestamp | grep -i "insufficient\|failedscheduling"