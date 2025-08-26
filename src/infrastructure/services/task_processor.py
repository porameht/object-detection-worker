import logging
import time
from datetime import datetime, UTC

from src.domain.entities.detection_result import ProcessingTask, ProcessingResult
from src.domain.entities.serializers import serialize_processing_result
from src.domain.repositories.detection_model import DetectionModel
from src.domain.repositories.image_repository import ImageRepository
from src.domain.repositories.callback_service import CallbackService

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Process detection tasks without database dependencies"""
    
    def __init__(
        self,
        detection_model: DetectionModel,
        image_repository: ImageRepository,
        callback_service: CallbackService,
    ):
        self._model = detection_model
        self._image_repo = image_repository
        self._callback_service = callback_service

    async def process_task(self, task: ProcessingTask) -> ProcessingResult:
        """Process a detection task"""
        start_time = time.time()
        
        try:
            # Process image
            image = await self._image_repo.retrieve_image(task.image_path)
            detections = self._model.predict(image)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            result = ProcessingResult(
                task_id=task.task_id,
                detections=detections,
                processed_at=datetime.now(UTC),
                processing_time_ms=processing_time_ms,
            )
            
            # Store results and send callback
            results_key = f"results/{task.task_id}/detection_results.json"
            results_data = serialize_processing_result(result)
            
            await self._image_repo.store_results(results_key, results_data)
            await self._callback_service.send_callback(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            raise