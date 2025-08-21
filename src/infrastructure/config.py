import os
from dataclasses import dataclass


@dataclass
class WorkerConfig:
    gcp_project_id: str
    gcs_bucket: str
    pubsub_subscription: str
    api_service_url: str
    confidence_threshold: float
    callback_timeout: int


def load_config() -> WorkerConfig:
    return WorkerConfig(
        gcp_project_id=os.getenv("GCP_PROJECT_ID", "your-gcp-project"),
        gcs_bucket=os.getenv("GCS_BUCKET", "object-detection-images"),
        pubsub_subscription=os.getenv("PUBSUB_SUBSCRIPTION", "detection-workers"),
        api_service_url=os.getenv("API_SERVICE_URL", "http://object-detection-api"),
        confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
        callback_timeout=int(os.getenv("CALLBACK_TIMEOUT", "30")),
    )