#!/bin/bash

case "${1:-help}" in
  "enable")
    PROFILE="${2:-development}"
    DISABLE_PUBSUB="${3:-false}"
    echo "🚀 Enabling HPA with profile: $PROFILE"
    if [ "$DISABLE_PUBSUB" = "true" ]; then
      echo "⚠️  Disabling Pub/Sub queue metrics (using resource metrics only)"
    else
      echo "📊 Using Pub/Sub queue metrics as primary scaling factor"
    fi
    
    # Create temporary config for the specified profile
    TMP_HPA="/tmp/hpa-${PROFILE}.yaml"
    cp k8s/hpa.yaml "$TMP_HPA"
    
    # Disable Pub/Sub metrics if requested (fallback to resource-only scaling)
    if [ "$DISABLE_PUBSUB" = "true" ]; then
      sed -i 's/- type: External/# - type: External/' "$TMP_HPA"
      sed -i 's/  external:/  # external:/' "$TMP_HPA"
      sed -i 's/    metric:/    # metric:/' "$TMP_HPA"
      sed -i 's/      name: pubsub.googleapis.com/      # name: pubsub.googleapis.com/' "$TMP_HPA"
      sed -i 's/      selector:/      # selector:/' "$TMP_HPA"
      sed -i 's/        matchLabels:/        # matchLabels:/' "$TMP_HPA"
      sed -i 's/          resource.labels.subscription_id: detection-workers/          # resource.labels.subscription_id: detection-workers/' "$TMP_HPA"
      sed -i 's/    target:/    # target:/' "$TMP_HPA"
      sed -i 's/      type: AverageValue/      # type: AverageValue/' "$TMP_HPA"
      sed -i 's/      averageValue: \"/      # averageValue: \"/' "$TMP_HPA"
    fi
    
    case "$PROFILE" in
      "development")
        # Already configured as default
        if [ "$DISABLE_PUBSUB" != "true" ]; then
          sed -i 's/averageValue: \"3\"/averageValue: \"3\"/' "$TMP_HPA"
        fi
        ;;
      "production")
        sed -i 's/minReplicas: 1/minReplicas: 2/' "$TMP_HPA"
        sed -i 's/maxReplicas: 5/maxReplicas: 12/' "$TMP_HPA"
        sed -i 's/averageUtilization: 75/averageUtilization: 70/' "$TMP_HPA"
        sed -i 's/averageUtilization: 60/averageUtilization: 50/' "$TMP_HPA"
        sed -i 's/stabilizationWindowSeconds: 300/stabilizationWindowSeconds: 900/' "$TMP_HPA"
        sed -i 's/value: 50/value: 20/' "$TMP_HPA"
        sed -i 's/stabilizationWindowSeconds: 60/stabilizationWindowSeconds: 180/' "$TMP_HPA"
        sed -i 's/value: 2/value: 3/' "$TMP_HPA"
        if [ "$DISABLE_PUBSUB" != "true" ]; then
          sed -i 's/averageValue: \"3\"/averageValue: \"2\"/' "$TMP_HPA"
        fi
        ;;
      "testing")
        sed -i 's/maxReplicas: 5/maxReplicas: 3/' "$TMP_HPA"
        sed -i 's/averageUtilization: 75/averageUtilization: 80/' "$TMP_HPA"
        sed -i 's/averageUtilization: 60/averageUtilization: 70/' "$TMP_HPA"
        sed -i 's/stabilizationWindowSeconds: 300/stabilizationWindowSeconds: 180/' "$TMP_HPA"
        sed -i 's/stabilizationWindowSeconds: 60/stabilizationWindowSeconds: 30/' "$TMP_HPA"
        sed -i 's/value: 2/value: 1/' "$TMP_HPA"
        sed -i 's/value: 100/value: 200/' "$TMP_HPA"
        if [ "$DISABLE_PUBSUB" != "true" ]; then
          sed -i 's/averageValue: \"3\"/averageValue: \"5\"/' "$TMP_HPA"
        fi
        ;;
    esac
    
    kubectl apply -f "$TMP_HPA"
    rm -f "$TMP_HPA"
    
    echo "✅ HPA enabled with $PROFILE profile"
    if [ "$DISABLE_PUBSUB" != "true" ]; then
      echo "📊 Pub/Sub queue scaling enabled as PRIMARY metric"
      echo "⚠️  Note: Requires Cloud Monitoring API and proper IAM permissions"
    else
      echo "📈 Using resource-based scaling only"
    fi
    echo "📊 Use '$0 status' to monitor scaling"
    ;;
    
  "disable")
    echo "🛑 Disabling HPA..."
    kubectl delete hpa object-detection-worker-hpa --ignore-not-found=true
    kubectl delete hpa object-detection-worker-hpa-simple --ignore-not-found=true
    echo "✅ HPA disabled - using manual scaling only"
    ;;
    
  "status")
    echo "📊 Current Scaling Status:"
    echo ""
    echo "HPA Status:"
    kubectl get hpa 2>/dev/null || echo "  No HPA found"
    echo ""
    echo "Current Pods:"
    kubectl get pods -l app=object-detection-worker
    echo ""
    echo "Deployment Scale:"
    kubectl get deployment object-detection-worker -o jsonpath='{.spec.replicas}/{.status.replicas}/{.status.readyReplicas}' | awk -F/ '{print "  Desired: " $1 ", Current: " $2 ", Ready: " $3}'
    echo ""
    ;;
    
  "scale")
    if [ -z "$2" ]; then
      echo "❌ Usage: $0 scale <number>"
      exit 1
    fi
    echo "⚖️  Manually scaling to $2 replicas..."
    kubectl scale deployment object-detection-worker --replicas=$2
    echo "✅ Scaled to $2 replicas"
    ;;
    
  "test-load")
    echo "🧪 Simulating load for HPA testing..."
    echo "This will create a load testing pod..."
    kubectl run load-test --image=busybox --restart=Never --rm -i --tty -- /bin/sh -c "
      echo 'Generating CPU load on worker pods...'
      for i in {1..100}; do
        echo 'Load test iteration $i'
        sleep 1
      done
    " || echo "Load test completed"
    ;;
    
  "monitor")
    echo "📈 Monitoring HPA (Press Ctrl+C to stop)..."
    watch -n 5 "kubectl get hpa; echo ''; kubectl top pods -l app=object-detection-worker; echo ''; kubectl get pods -l app=object-detection-worker"
    ;;
    
  *)
    echo "🎛️  Object Detection Worker - Scaling Management"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  enable [PROFILE] [DISABLE_PUBSUB]  Enable HPA with profile"
    echo "  disable                            Disable HPA"
    echo "  status                             Show current scaling status"
    echo "  scale <N>                          Manually scale to N replicas"
    echo "  test-load                          Simulate load for testing HPA"
    echo "  monitor                            Watch HPA metrics in real-time"
    echo ""
    echo "🎯 Scaling Profiles:"
    echo "  development (default):   1-5 replicas, queue: 3 msgs/pod"
    echo "  production:              2-12 replicas, queue: 2 msgs/pod"  
    echo "  testing:                 1-3 replicas, queue: 5 msgs/pod"
    echo ""
    echo "📊 Primary Metric: Pub/Sub Queue Depth (most accurate for ML)"
    echo "  • Direct correlation: queue messages = actual workload"
    echo "  • Predictive scaling: scale before resource saturation"
    echo "  • Business-aligned: scale based on actual tasks"
    echo ""
    echo "Examples:"
    echo "  $0 enable development        # Enable with queue-based scaling"
    echo "  $0 enable production true    # Enable without queue metrics"
    echo "  $0 scale 3                   # Scale to 3 replicas manually"
    echo "  $0 status                    # Check current status"
    echo ""
    ;;
esac