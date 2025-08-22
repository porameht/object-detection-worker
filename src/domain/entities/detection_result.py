from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox


@dataclass
class ProcessingTask:
    task_id: UUID
    image_path: str
    callback_url: str = None


@dataclass
class ProcessingResult:
    task_id: UUID
    detections: List[Detection]
    processed_at: datetime
    processing_time_ms: int