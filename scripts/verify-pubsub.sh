#!/bin/bash

PROJECT_ID="processing-469712"

echo "=== Verifying Pub/Sub Setup ==="

# Check topics
echo "Topics:"
gcloud pubsub topics list --project=$PROJECT_ID

# Check subscriptions
echo -e "\nSubscriptions:"
gcloud pubsub subscriptions list --project=$PROJECT_ID

# Check if detection-workers subscription exists
echo -e "\nDetection Workers Subscription Details:"
gcloud pubsub subscriptions describe detection-workers \
  --project=$PROJECT_ID 2>/dev/null || {
    echo "Subscription 'detection-workers' not found!"
    echo "Creating subscription..."
    gcloud pubsub subscriptions create detection-workers \
      --topic=object-detection-tasks \
      --project=$PROJECT_ID \
      --ack-deadline=60 \
      --max-delivery-attempts=5 \
      --message-retention-duration=10m
}

# Test publishing a message
echo -e "\nTesting Pub/Sub connectivity..."
TEST_MESSAGE='{"test": "message", "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}'
gcloud pubsub topics publish object-detection-tasks \
  --message="$TEST_MESSAGE" \
  --project=$PROJECT_ID && echo "✓ Successfully published test message"

# Check for pending messages
echo -e "\nChecking for pending messages:"
gcloud pubsub subscriptions pull detection-workers \
  --project=$PROJECT_ID \
  --auto-ack \
  --limit=1 || echo "No pending messages"

echo -e "\nPub/Sub verification complete!"