import asyncio
import json
import logging
from uuid import UUID

import boto3
import redis.asyncio as redis

from .domain.entities.detection_result import ProcessingTask
from .application.use_cases.process_detection_task import ProcessDetectionTaskUseCase
from .infrastructure.config import load_config
from .infrastructure.models.rfdetr_model import RFDETRModel
from .infrastructure.repositories.s3_image_repository import S3ImageRepository
from .infrastructure.repositories.redis_task_repository import RedisTaskRepository
from .infrastructure.services.http_callback_service import HttpCallbackService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ObjectDetectionWorker:
    def __init__(self):
        self._config = load_config()
        self._setup_dependencies()

    def _setup_dependencies(self):
        redis_client = redis.from_url(self._config.redis_url)
        s3_client = boto3.client('s3', region_name=self._config.aws_region)
        
        detection_model = RFDETRModel(self._config.confidence_threshold)
        image_repository = S3ImageRepository(s3_client, self._config.s3_bucket)
        task_repository = RedisTaskRepository(redis_client)
        callback_service = HttpCallbackService(self._config.callback_timeout)
        
        self._process_task_use_case = ProcessDetectionTaskUseCase(
            detection_model,
            image_repository,
            task_repository,
            callback_service,
        )
        
        self._redis_client = redis_client

    async def _dequeue_task(self) -> ProcessingTask:
        result = await self._redis_client.brpop(self._config.queue_name, timeout=10)
        if result:
            _, task_json = result
            task_data = json.loads(task_json)
            return ProcessingTask(
                task_id=UUID(task_data["task_id"]),
                image_key=task_data["image_key"],
                callback_url=task_data.get("callback_url"),
            )
        return None

    async def run(self):
        logger.info("Starting object detection worker...")
        
        while True:
            try:
                task = await self._dequeue_task()
                
                if task:
                    logger.info(f"Processing task {task.task_id}")
                    await self._process_task_use_case.execute(task)
                    logger.info(f"Task {task.task_id} completed")
                
            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                continue


async def main():
    worker = ObjectDetectionWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())