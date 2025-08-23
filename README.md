# Object Detection Worker

ML Worker for object detection at scale. Pulls tasks from Pub/Sub, reads images from GCS, runs RFDETR, stores results to GCS, and notifies an internal API.

<img width="746" height="394" alt="Screenshot 2568-08-23 at 16 04 01" src="https://github.com/user-attachments/assets/cab74297-1c3c-4103-a8f2-a2ff043e18e3" />

## What it does

- Consume tasks from Pub/Sub subscription
- Download image from GCS (`image_path`)
- Run detection with RFDETR
- Store JSON results to `results/<task_id>/detection_results.json` in GCS
- POST result summary to internal API

## Features

- Pub/Sub driven worker
- GCS I/O (images, results)
- Internal API callback
- Docker + Kubernetes ready

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud: Pub/Sub + Storage
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

3. **Run tests (optional)**:
   ```bash
   pytest -q
   ```

4. **Run the worker**:
   ```bash
   python -m src.main
   ```

### Docker

```bash
# Build image
docker build -t object-detection-worker .

# Run container
docker run --env-file .env object-detection-worker
```

### Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/
```

## Configuration (env)

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud Project ID | `your-gcp-project` |
| `GCS_BUCKET` | GCS bucket name | `object-detection-images` |
| `PUBSUB_SUBSCRIPTION` | Pub/Sub subscription | `detection-workers` |
| `API_SERVICE_URL` | Internal API base URL | `http://object-detection-api` |
| `CONFIDENCE_THRESHOLD` | Detection threshold | `0.5` |
| `CALLBACK_TIMEOUT` | Callback timeout (s) | `30` |

## Task format

Publish a message to Pub/Sub with:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "image_path": "images/photo.jpg"
}
```

Result JSON stored in GCS:

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

## Structure

```
src/
├── main.py
├── domain/
│   ├── entities/
│   └── repositories/
└── infrastructure/
    ├── config.py
    ├── models/
    ├── repositories/
    └── services/
```

## Testing

```bash
pytest -q
```

## Deploy (CI/CD)

GitHub Actions workflow `.github/workflows/deploy.yml`:

- Job 1: run tests → `pytest tests/ --verbose`
- Job 2: build & push Docker to GAR
- Apply K8s manifests with updated image

## Scaling (optional)

K8s HPA manifests included under `k8s/`. Tune based on Pub/Sub queue depth and resource usage.

## Logs

INFO-level logs for task start/end, errors, and processing time.
