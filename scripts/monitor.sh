#!/bin/bash

# Monitoring and Troubleshooting Script
# Usage: ./scripts/monitor.sh [command]

NAMESPACE="object-detection"
APP_NAME="object-detection-worker"

case "$1" in
    "logs")
        echo "Showing logs for $APP_NAME..."
        kubectl logs -f deployment/$APP_NAME -n $NAMESPACE
        ;;
    "status")
        echo "=== Deployment Status ==="
        kubectl get deployment $APP_NAME -n $NAMESPACE
        echo ""
        echo "=== Pods ==="
        kubectl get pods -n $NAMESPACE -l app=$APP_NAME
        echo ""
        echo "=== HPA Status ==="
        kubectl get hpa -n $NAMESPACE
        echo ""
        echo "=== Events ==="
        kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -10
        ;;
    "describe")
        echo "=== Deployment Description ==="
        kubectl describe deployment $APP_NAME -n $NAMESPACE
        echo ""
        echo "=== Pod Descriptions ==="
        kubectl describe pods -n $NAMESPACE -l app=$APP_NAME
        ;;
    "scale")
        if [ -z "$2" ]; then
            echo "Usage: $0 scale [replicas]"
            exit 1
        fi
        echo "Scaling $APP_NAME to $2 replicas..."
        kubectl scale deployment $APP_NAME --replicas=$2 -n $NAMESPACE
        kubectl rollout status deployment/$APP_NAME -n $NAMESPACE
        ;;
    "restart")
        echo "Restarting $APP_NAME deployment..."
        kubectl rollout restart deployment/$APP_NAME -n $NAMESPACE
        kubectl rollout status deployment/$APP_NAME -n $NAMESPACE
        ;;
    "shell")
        POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=$APP_NAME -o jsonpath='{.items[0].metadata.name}')
        if [ -z "$POD_NAME" ]; then
            echo "No pods found for $APP_NAME"
            exit 1
        fi
        echo "Opening shell in pod: $POD_NAME"
        kubectl exec -it $POD_NAME -n $NAMESPACE -- /bin/bash
        ;;
    "test")
        echo "Running connectivity tests..."
        kubectl run test-pod --image=busybox -n $NAMESPACE --rm -it --restart=Never -- sh -c "
            echo 'Testing DNS resolution...'
            nslookup google.com
            echo 'Testing GCS connectivity...'
            nc -zv storage.googleapis.com 443 || echo 'GCS connection test completed'
            echo 'Testing Pub/Sub connectivity...'
            nc -zv pubsub.googleapis.com 443 || echo 'Pub/Sub connection test completed'
        "
        ;;
    "resource-usage")
        echo "=== Resource Usage ==="
        kubectl top pods -n $NAMESPACE -l app=$APP_NAME
        echo ""
        echo "=== Node Resource Usage ==="
        kubectl top nodes
        ;;
    *)
        echo "Monitoring script for $APP_NAME"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  logs            - Show live logs"
        echo "  status          - Show deployment status"
        echo "  describe        - Describe deployment and pods"
        echo "  scale [num]     - Scale deployment to [num] replicas"
        echo "  restart         - Restart deployment"
        echo "  shell           - Open shell in a pod"
        echo "  test            - Run connectivity tests"
        echo "  resource-usage  - Show resource usage"
        echo ""
        echo "Examples:"
        echo "  $0 logs"
        echo "  $0 scale 5"
        echo "  $0 status"
        ;;
esac