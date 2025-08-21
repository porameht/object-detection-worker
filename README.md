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

## Monitoring

The worker logs processing events at INFO level:

- Task start/completion
- Error handling
- Performance metrics (processing time)