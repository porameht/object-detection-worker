import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from uuid import uuid4

from src.infrastructure.services.task_processor import TaskProcessor
from src.domain.entities.detection_result import (
    ProcessingTask,
    Detection,
    BoundingBox,
)


@pytest.fixture
def mocks():
    model = Mock()
    model.predict.return_value = [Detection(
        class_id=1, class_name="person", confidence=0.95,
        bbox=BoundingBox(x1=10.0, y1=20.0, x2=100.0, y2=200.0)
    )]
    
    repo = Mock()
    repo.retrieve_image = AsyncMock(return_value=b"fake_image")
    repo.store_results = AsyncMock()
    
    callback = Mock()
    callback.send_callback = AsyncMock()
    
    processor = TaskProcessor(model, repo, callback)
    return processor, model, repo, callback


@pytest.mark.asyncio
async def test_successful_processing(mocks):
    """Test complete successful processing flow"""
    processor, model, repo, callback = mocks
    task = ProcessingTask(task_id=uuid4(), image_path="test.jpg")
    
    result = await processor.process_task(task)
    
    assert result.task_id == task.task_id
    assert len(result.detections) == 1
    assert result.detections[0].class_name == "person"
    assert isinstance(result.processed_at, datetime)
    
    repo.retrieve_image.assert_called_once_with("test.jpg")
    model.predict.assert_called_once()
    repo.store_results.assert_called_once()
    callback.send_callback.assert_called_once()


@pytest.mark.asyncio
async def test_image_not_found(mocks):
    """Test error when image retrieval fails"""
    processor, _, repo, _ = mocks
    repo.retrieve_image.side_effect = Exception("Image not found")
    
    task = ProcessingTask(task_id=uuid4(), image_path="missing.jpg")
    
    with pytest.raises(Exception, match="Image not found"):
        await processor.process_task(task)


@pytest.mark.asyncio
async def test_empty_detections(mocks):
    """Test processing with no objects detected"""
    processor, model, _, _ = mocks
    model.predict.return_value = []
    
    task = ProcessingTask(task_id=uuid4(), image_path="empty.jpg")
    result = await processor.process_task(task)
    
    assert len(result.detections) == 0
    assert result.processing_time_ms >= 0
