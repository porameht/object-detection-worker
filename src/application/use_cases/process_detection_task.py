import time
from datetime import datetime
from typing import List
from uuid import UUID

from ...domain.entities.detection_result import ProcessingTask, ProcessingResult, Detection
from ...domain.repositories.detection_model import DetectionModel
from ...domain.repositories.image_repository import ImageRepository
from ...domain.repositories.task_repository import TaskRepository
from ...domain.repositories.callback_service import CallbackService


class ProcessDetectionTaskUseCase:
    def __init__(
        self,
        detection_model: DetectionModel,
        image_repository: ImageRepository,
        task_repository: TaskRepository,
        callback_service: CallbackService,
    ):
        self._model = detection_model
        self._image_repo = image_repository
        self._task_repo = task_repository
        self._callback_service = callback_service

    async def execute(self, task: ProcessingTask) -> ProcessingResult:
        start_time = time.time()
        
        try:
            await self._task_repo.update_task_status(task.task_id, "processing")
            
            image = await self._image_repo.retrieve_image(task.image_path)
            
            detections = self._model.predict(image)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            result = ProcessingResult(
                task_id=task.task_id,
                detections=detections,
                processed_at=datetime.utcnow(),
                processing_time_ms=processing_time_ms,
            )
            
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
            await self._task_repo.update_task_status(task.task_id, "completed", result)
            
            await self._callback_service.send_callback(result)
            
            return result
            
        except Exception as e:
            await self._task_repo.update_task_status(task.task_id, "failed")
            raise