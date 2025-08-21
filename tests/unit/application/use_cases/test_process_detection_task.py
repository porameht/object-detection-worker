import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from uuid import uuid4

from src.application.use_cases.process_detection_task import ProcessDetectionTaskUseCase
from src.domain.entities.detection_result import (
    ProcessingTask,
    ProcessingResult,
    Detection,
    BoundingBox,
)


@pytest.fixture
def mock_detection_model():
    model = Mock()
    model.predict.return_value = [
        Detection(
            class_id=1,
            class_name="person",
            confidence=0.95,
            bbox=BoundingBox(x1=10.0, y1=20.0, x2=100.0, y2=200.0)
        )
    ]
    return model


@pytest.fixture
def mock_image_repository():
    repo = Mock()
    repo.retrieve_image = AsyncMock(return_value=b"fake_image_data")
    repo.store_results = AsyncMock()
    return repo


@pytest.fixture
def mock_task_repository():
    repo = Mock()
    repo.update_task_status = AsyncMock()
    return repo


@pytest.fixture
def mock_callback_service():
    service = Mock()
    service.send_callback = AsyncMock()
    return service


@pytest.fixture
def use_case(mock_detection_model, mock_image_repository, mock_task_repository, mock_callback_service):
    return ProcessDetectionTaskUseCase(
        detection_model=mock_detection_model,
        image_repository=mock_image_repository,
        task_repository=mock_task_repository,
        callback_service=mock_callback_service,
    )


@pytest.mark.asyncio
async def test_execute_successful_processing(use_case, mock_detection_model, mock_image_repository, mock_task_repository, mock_callback_service):
    task_id = uuid4()
    task = ProcessingTask(
        task_id=task_id,
        image_key="test-image.jpg",
        callback_url="http://example.com/callback"
    )
    
    result = await use_case.execute(task)
    
    assert result.task_id == task_id
    assert len(result.detections) == 1
    assert result.detections[0].class_name == "person"
    assert result.processing_time_ms >= 0
    assert isinstance(result.processed_at, datetime)
    
    mock_task_repository.update_task_status.assert_any_call(task_id, "processing")
    mock_task_repository.update_task_status.assert_any_call(task_id, "completed", result)
    mock_image_repository.retrieve_image.assert_called_once_with("test-image.jpg")
    mock_detection_model.predict.assert_called_once()
    mock_callback_service.send_callback.assert_called_once_with("http://example.com/callback", result)


@pytest.mark.asyncio
async def test_execute_without_callback_url(use_case, mock_detection_model, mock_image_repository, mock_task_repository, mock_callback_service):
    task_id = uuid4()
    task = ProcessingTask(
        task_id=task_id,
        image_key="test-image.jpg"
    )
    
    result = await use_case.execute(task)
    
    assert result.task_id == task_id
    mock_callback_service.send_callback.assert_not_called()


@pytest.mark.asyncio
async def test_execute_handles_exception(use_case, mock_detection_model, mock_image_repository, mock_task_repository, mock_callback_service):
    task_id = uuid4()
    task = ProcessingTask(
        task_id=task_id,
        image_key="test-image.jpg"
    )
    
    mock_image_repository.retrieve_image.side_effect = Exception("Image not found")
    
    with pytest.raises(Exception, match="Image not found"):
        await use_case.execute(task)
    
    mock_task_repository.update_task_status.assert_any_call(task_id, "failed")