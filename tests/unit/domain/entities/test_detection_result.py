import pytest
from datetime import datetime
from uuid import uuid4

from src.domain.entities.detection_result import (
    BoundingBox,
    Detection,
    ProcessingTask,
    ProcessingResult,
)


class TestBoundingBox:
    def test_bounding_box_creation(self):
        bbox = BoundingBox(x1=10.0, y1=20.0, x2=100.0, y2=200.0)
        
        assert bbox.x1 == 10.0
        assert bbox.y1 == 20.0
        assert bbox.x2 == 100.0
        assert bbox.y2 == 200.0


class TestDetection:
    def test_detection_creation(self):
        bbox = BoundingBox(x1=10.0, y1=20.0, x2=100.0, y2=200.0)
        detection = Detection(
            class_id=1,
            class_name="person",
            confidence=0.95,
            bbox=bbox
        )
        
        assert detection.class_id == 1
        assert detection.class_name == "person"
        assert detection.confidence == 0.95
        assert detection.bbox == bbox


class TestProcessingTask:
    def test_processing_task_creation(self):
        task_id = uuid4()
        task = ProcessingTask(
            task_id=task_id,
            image_path="test-image.jpg"
        )
        
        assert task.task_id == task_id
        assert task.image_path == "test-image.jpg"


class TestProcessingResult:
    def test_processing_result_creation(self):
        task_id = uuid4()
        bbox = BoundingBox(x1=10.0, y1=20.0, x2=100.0, y2=200.0)
        detection = Detection(
            class_id=1,
            class_name="person",
            confidence=0.95,
            bbox=bbox
        )
        processed_at = datetime.utcnow()
        
        result = ProcessingResult(
            task_id=task_id,
            detections=[detection],
            processed_at=processed_at,
            processing_time_ms=500
        )
        
        assert result.task_id == task_id
        assert len(result.detections) == 1
        assert result.detections[0] == detection
        assert result.processed_at == processed_at
        assert result.processing_time_ms == 500