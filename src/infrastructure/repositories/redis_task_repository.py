import json
from datetime import datetime
from uuid import UUID
import redis.asyncio as redis

from ...domain.entities.detection_result import ProcessingResult
from ...domain.repositories.task_repository import TaskRepository


class RedisTaskRepository(TaskRepository):
    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    async def update_task_status(
        self, task_id: UUID, status: str, result: ProcessingResult = None
    ) -> None:
        key = f"task:{task_id}"
        
        existing_data = await self._redis.get(key)
        if not existing_data:
            return
            
        task_data = json.loads(existing_data)
        task_data["status"] = status
        task_data["updated_at"] = datetime.utcnow().isoformat()
        
        if result:
            task_data["result"] = {
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
        
        await self._redis.setex(key, 3600, json.dumps(task_data))