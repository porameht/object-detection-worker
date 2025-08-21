import os
from dataclasses import dataclass


@dataclass
class WorkerConfig:
    gcp_project_id: str
    gcs_bucket: str
    redis_url: str
    queue_name: str
    confidence_threshold: float
    callback_timeout: int


def load_config() -> WorkerConfig:
    return WorkerConfig(
        gcp_project_id=os.getenv("GCP_PROJECT_ID", "your-gcp-project"),
        gcs_bucket=os.getenv("GCS_BUCKET", "object-detection-images"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        queue_name=os.getenv("QUEUE_NAME", "detection_queue"),
        confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
        callback_timeout=int(os.getenv("CALLBACK_TIMEOUT", "30")),
    )