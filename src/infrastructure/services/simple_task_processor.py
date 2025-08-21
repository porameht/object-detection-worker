import logging
from ...domain.entities.detection_result import ProcessingTask, ProcessingResult
from ...domain.repositories.detection_model import DetectionModel
from ...domain.repositories.image_repository import ImageRepository
from ...domain.repositories.callback_service import CallbackService

logger = logging.getLogger(__name__)


class SimpleTaskProcessor:
    """Simple task processor without database dependencies"""
    
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
        import time
        from datetime import datetime
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting processing task {task.task_id}")
            
            # Retrieve and process image
            image = await self._image_repo.retrieve_image(task.image_key)
            detections = self._model.predict(image)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            result = ProcessingResult(
                task_id=task.task_id,
                detections=detections,
                processed_at=datetime.utcnow(),
                processing_time_ms=processing_time_ms,
            )
            
            # Store results in GCS
            results_key = f"results/{task.task_id}/detection_results.json"
            results_data = {
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
            
            await self._image_repo.store_results(results_key, results_data)
            
            # Send callback notification
            if task.callback_url:
                await self._callback_service.send_callback(task.callback_url, result)
            
            logger.info(f"Task {task.task_id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            raise