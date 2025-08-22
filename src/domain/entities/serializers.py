"""Serialization utilities for domain entities"""

from typing import Dict, Any
from .detection_result import ProcessingResult


def serialize_processing_result(result: ProcessingResult) -> Dict[str, Any]:
    """Convert ProcessingResult to JSON-serializable dict"""
    return {
        "task_id": str(result.task_id),
        "detections": [
            {
                "class_id": d.class_id,
                "class_name": d.class_name,
                "confidence": d.confidence,
                "bbox": {
                    "x1": d.bbox.x1,
                    "y1": d.bbox.y1,
                    "x2": d.bbox.x2,
                    "y2": d.bbox.y2,
                },
            }
            for d in result.detections
        ],
        "processed_at": result.processed_at.isoformat(),
        "processing_time_ms": result.processing_time_ms,
    }
