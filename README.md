# Object Detection Worker

A scalable, containerized worker service for processing object detection tasks using the RT-DETR model. The service processes images from S3, performs object detection, and stores results back to S3 with optional HTTP callbacks.

## Architecture

The application follows Clean Architecture principles with clear separation of concerns:

- **Domain**: Core business entities and repository interfaces
- **Application**: Use cases and business logic
- **Infrastructure**: External service implementations (Pub/Sub, GCS, HTTP)

## Features

- **Real-time Object Detection**: Uses RT-DETR model for accurate object detection
- **Queue-based Processing**: Pub/Sub-backed task queue for scalable processing
- **Cloud Storage**: GCS integration for image input and result storage
- **HTTP Callbacks**: Optional webhook notifications on task completion
- **Clean Architecture**: Maintainable, testable codebase with dependency injection
- **Docker Support**: Multi-stage builds optimized for production
- **Kubernetes Ready**: Complete K8s manifests for deployment

## Quick Start

### Prerequisites

- Python 3.12+
- Docker (optional)
- Google Cloud Project with Pub/Sub and Storage APIs enabled
- GCS bucket

### Local Development
1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd object-detection-worker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the worker**:
   ```bash
   python -m src.main
   ```

### Docker Deployment

```bash
# Build image
docker build -t object-detection-worker .

# Run container
docker run --env-file .env object-detection-worker
```

### Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/
```

## Configuration

All configuration is handled through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud Project ID | - |
| `GCS_BUCKET` | GCS bucket for images and results | `object-detection-images` |
| `PUBSUB_TOPIC` | Pub/Sub topic name | `object-detection-tasks` |
| `CONFIDENCE_THRESHOLD` | Detection confidence threshold | `0.5` |
| `CALLBACK_TIMEOUT` | HTTP callback timeout (seconds) | `30` |

## Task Processing

### Input Format

Tasks are JSON objects published to the Pub/Sub topic:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "image_key": "images/photo.jpg",
  "callback_url": "https://api.example.com/webhooks/detection"
}
```

### Output Format

Results are stored in GCS as JSON:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.85,
      "bbox": {
        "x1": 100.0,
        "y1": 150.0,
        "x2": 200.0,
        "y2": 300.0
      }
    }
  ],
  "processed_at": "2024-01-01T12:00:00Z",
  "processing_time_ms": 1500
}
```

## Project Structure

```
src/
├── main.py                 # Application entry point
├── domain/                 # Core business logic
│   ├── entities/          # Domain entities
│   └── repositories/      # Repository interfaces
├── application/           # Use cases
│   └── use_cases/        
├── infrastructure/        # External services
│   ├── config.py         # Configuration
│   ├── models/           # ML model implementations
│   ├── repositories/     # Repository implementations
│   └── services/         # External service clients
└── __init__.py
```

## Development

### Testing

```bash
# Run tests (configure test command in your environment)
pytest  # or your preferred test runner
```

## Deployment

The service includes production-ready configurations:

- **Multi-stage Docker builds** for optimized images
- **Kubernetes manifests** with proper resource limits
- **ConfigMaps and Secrets** for environment configuration
- **RBAC** for secure cluster access

## Scaling Management

The worker includes an intelligent Horizontal Pod Autoscaler (HPA) optimized specifically for ML image processing workloads.

### Why Pub/Sub Queue Depth is Primary Metric

**Traditional resource-based scaling (Memory/CPU):**
- ❌ **Reactive**: Scales after resources are saturated
- ❌ **Delayed**: Users wait 2-3 minutes for model startup
- ❌ **Inaccurate**: Resource usage varies by image complexity

**Queue-based scaling (Pub/Sub messages):**
- ✅ **Predictive**: Scales before bottlenecks occur
- ✅ **Immediate**: Fast response to traffic spikes
- ✅ **Accurate**: 1 message = 1 image = predictable workload

### Scaling Logic Priority

1. **Primary**: Pub/Sub Queue Depth (most accurate)
   - Direct correlation: queue messages = actual work waiting
   - Business-aligned: scale based on real user demand
   - Predictive: scale before resource saturation

2. **Secondary**: Memory Usage (critical for ML models)
   - ML models require significant memory for inference
   - Memory exhaustion causes pod crashes (OOMKilled)

3. **Tertiary**: CPU Usage (backup metric)
   - Less critical for inference workloads
   - Used as fallback when queue metrics unavailable

### Usage Examples

```bash
# Enable queue-based scaling (recommended)
./scripts/manage-scaling.sh enable development        # 1-5 pods, 3 msgs/pod
./scripts/manage-scaling.sh enable production         # 2-12 pods, 2 msgs/pod
./scripts/manage-scaling.sh enable testing            # 1-3 pods, 5 msgs/pod

# Fallback to resource-only scaling
./scripts/manage-scaling.sh enable production true    # Disable queue metrics

# Monitoring and management
./scripts/manage-scaling.sh monitor                   # Real-time HPA metrics
./scripts/manage-scaling.sh status                    # Current scaling status
./scripts/manage-scaling.sh scale 5                   # Manual scaling override
```

### Scaling Profiles

| Profile | Min/Max Pods | Queue Threshold | Memory | CPU | Use Case |
|---------|--------------|-----------------|--------|-----|----------|
| **development** | 1-5 | 3 msgs/pod | 75% | 60% | Testing, low traffic |
| **production** | 2-12 | 2 msgs/pod | 70% | 50% | Production workloads |
| **testing** | 1-3 | 5 msgs/pod | 80% | 70% | CI/CD, automated tests |

### Real-world Scenario

**Morning rush**: 1000 users upload images simultaneously

**Queue-based scaling response:**
1. Queue depth: 1000 messages detected
2. HPA calculates: 1000 ÷ 2 = 500 pods needed (production profile)
3. Scales to maxReplicas: 12 pods immediately
4. Users see results within 30 seconds

**Resource-based scaling response:**
1. Single pod starts processing → Memory/CPU spike
2. HPA triggers scale-up after 60-300s delay
3. New pods take 2-3 minutes to load ML model
4. Users wait 5+ minutes for results

### Cost Optimization

- **Aggressive scale-down**: When queue is empty, scale to minimum replicas
- **Conservative scale-up**: Gradual increase to handle sustained load
- **Smart thresholds**: Different profiles for different traffic patterns

## Monitoring

The worker logs processing events at INFO level:

- Task start/completion
- Error handling
- Performance metrics (processing time)
