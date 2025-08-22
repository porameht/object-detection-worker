import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from src.infrastructure.services.task_processor import TaskProcessor
from src.domain.entities.detection_result import ProcessingTask, Detection, BoundingBox


@pytest.fixture
def integration_mocks():
    """Setup complete integration test mocks"""
    model = Mock()
    model.predict.return_value = [
        Detection(0, "person", 0.92, BoundingBox(100.0, 150.0, 250.0, 400.0)),
        Detection(2, "car", 0.88, BoundingBox(350.0, 200.0, 550.0, 350.0))
    ]
    
    repo = Mock()
    repo.retrieve_image = AsyncMock(return_value=b"fake_image_data")
    repo.store_results = AsyncMock()
    
    callback = Mock()
    callback.send_callback = AsyncMock()
    
    processor = TaskProcessor(model, repo, callback)
    return processor, model, repo, callback


@pytest.mark.asyncio
async def test_end_to_end_pipeline(integration_mocks):
    """Test complete pipeline from task to callback"""
    processor, model, repo, callback = integration_mocks
    task_id = uuid4()
    
    task = ProcessingTask(task_id=task_id, image_path="test-images/sample.jpg")
    result = await processor.process_task(task)
    
    # Verify complete flow
    assert result.task_id == task_id
    assert len(result.detections) == 2
    
    person = next(d for d in result.detections if d.class_name == "person")
    assert person.confidence == 0.92
    
    # Verify all services called correctly
    repo.retrieve_image.assert_called_once_with("test-images/sample.jpg")
    model.predict.assert_called_once()
    repo.store_results.assert_called_once()
    callback.send_callback.assert_called_once_with(result)
    
    # Verify stored data format
    store_args = repo.store_results.call_args[0]
    results_key, results_data = store_args
    assert f"results/{task_id}/detection_results.json" == results_key
    assert len(results_data["detections"]) == 2


@pytest.mark.asyncio
async def test_error_propagation(integration_mocks):
    """Test that errors propagate correctly through pipeline"""
    processor, _, repo, _ = integration_mocks
    
    repo.retrieve_image.side_effect = FileNotFoundError("Image not found")
    task = ProcessingTask(task_id=uuid4(), image_path="missing.jpg")
    
    with pytest.raises(FileNotFoundError):
        await processor.process_task(task)


@pytest.mark.asyncio
async def test_timing_accuracy(integration_mocks):
    """Test processing time tracking"""
    processor, model, repo, _ = integration_mocks
    model.predict.return_value = []
    
    task = ProcessingTask(task_id=uuid4(), image_path="test.jpg")
    result = await processor.process_task(task)
    
    assert result.processing_time_ms >= 0
    assert result.processed_at is not None
