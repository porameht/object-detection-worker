from datetime import datetime
from uuid import uuid4

from src.domain.entities.serializers import serialize_processing_result
from src.domain.entities.detection_result import (
    ProcessingResult,
    Detection,
    BoundingBox,
)


def test_serialize_with_detections():
    """Test serialization with detection data"""
    task_id = uuid4()
    detection = Detection(
        class_id=1, class_name="person", confidence=0.95,
        bbox=BoundingBox(x1=10.5, y1=20.3, x2=100.7, y2=200.9)
    )
    
    result = ProcessingResult(
        task_id=task_id,
        detections=[detection],
        processed_at=datetime(2024, 1, 15, 10, 30, 45),
        processing_time_ms=1500
    )
    
    serialized = serialize_processing_result(result)
    
    assert serialized["task_id"] == str(task_id)
    assert serialized["processing_time_ms"] == 1500
    assert serialized["processed_at"] == "2024-01-15T10:30:45"
    
    det = serialized["detections"][0]
    assert det["class_name"] == "person"
    assert det["confidence"] == 0.95
    assert det["bbox"]["x1"] == 10.5


def test_serialize_empty_detections():
    """Test serialization with no detections"""
    result = ProcessingResult(
        task_id=uuid4(),
        detections=[],
        processed_at=datetime(2024, 1, 15, 10, 30, 45),
        processing_time_ms=500
    )
    
    serialized = serialize_processing_result(result)
    
    assert len(serialized["detections"]) == 0
    assert serialized["processing_time_ms"] == 500


def test_serialize_multiple_detections():
    """Test serialization with multiple objects"""
    detections = [
        Detection(1, "person", 0.95, BoundingBox(10.0, 20.0, 100.0, 200.0)),
        Detection(2, "car", 0.88, BoundingBox(150.0, 50.0, 300.0, 180.0))
    ]
    
    result = ProcessingResult(
        task_id=uuid4(),
        detections=detections,
        processed_at=datetime(2024, 1, 15, 10, 30, 45),
        processing_time_ms=2000
    )
    
    serialized = serialize_processing_result(result)
    
    assert len(serialized["detections"]) == 2
    assert serialized["detections"][0]["class_name"] == "person"
    assert serialized["detections"][1]["class_name"] == "car"
