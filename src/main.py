import asyncio
import json
import logging
from uuid import UUID

from google.cloud import storage

from .domain.entities.detection_result import ProcessingTask
from .infrastructure.services.simple_task_processor import SimpleTaskProcessor
from .infrastructure.config import load_config
from .infrastructure.models.rfdetr_model import RFDETRModel
from .infrastructure.repositories.gcs_image_repository import GCSImageRepository
from .infrastructure.repositories.pubsub_task_processor import PubSubTaskProcessor
from .infrastructure.services.internal_api_callback_service import InternalAPICallbackService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ObjectDetectionWorker:
    def __init__(self):
        self._config = load_config()
        self._setup_dependencies()

    def _setup_dependencies(self):
        gcs_client = storage.Client(project=self._config.gcp_project_id)
        
        detection_model = RFDETRModel(self._config.confidence_threshold)
        image_repository = GCSImageRepository(gcs_client, self._config.gcs_bucket)
        callback_service = InternalAPICallbackService(
            self._config.api_service_url,
            self._config.callback_timeout
        )
        
        self._task_processor_service = SimpleTaskProcessor(
            detection_model,
            image_repository,
            callback_service,
        )
        
        self._pubsub_processor = PubSubTaskProcessor(
            self._config.gcp_project_id,
            self._config.pubsub_subscription
        )

    def _handle_task(self, task: ProcessingTask):
        """Handle a single task - called by Pub/Sub processor"""
        try:
            logger.info(f"Processing task {task.task_id}")
            
            # Run the async task processor in sync context
            import asyncio
            asyncio.run(self._task_processor_service.process_task(task))
            
            logger.info(f"Task {task.task_id} completed")
            
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {e}")
            raise  # Re-raise to trigger message nack

    def run(self):
        """Start the worker using Pub/Sub message consumption"""
        logger.info("Starting object detection worker with Pub/Sub...")
        
        try:
            # Start consuming messages - this will block
            self._pubsub_processor.start_consuming(self._handle_task)
            
        except KeyboardInterrupt:
            logger.info("Worker shutting down...")
        except Exception as e:
            logger.error(f"Worker error: {e}")
            raise


def main():
    worker = ObjectDetectionWorker()
    worker.run()


if __name__ == "__main__":
    main()