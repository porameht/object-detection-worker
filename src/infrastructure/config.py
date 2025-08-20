import os
from dataclasses import dataclass


@dataclass
class WorkerConfig:
    aws_region: str
    s3_bucket: str
    redis_url: str
    queue_name: str
    confidence_threshold: float
    callback_timeout: int


def load_config() -> WorkerConfig:
    return WorkerConfig(
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        s3_bucket=os.getenv("S3_BUCKET", "object-detection-images"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        queue_name=os.getenv("QUEUE_NAME", "detection_queue"),
        confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
        callback_timeout=int(os.getenv("CALLBACK_TIMEOUT", "30")),
    )