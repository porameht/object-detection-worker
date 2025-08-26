import json
import logging
from typing import Callable
from uuid import UUID

from google.cloud import pubsub_v1

from src.domain.entities.detection_result import ProcessingTask

logger = logging.getLogger(__name__)


class PubSubTaskProcessor:
    def __init__(self, project_id: str, subscription_name: str = "detection-workers"):
        self._project_id = project_id
        self._subscription_name = subscription_name
        self._subscriber = pubsub_v1.SubscriberClient()
        self._subscription_path = self._subscriber.subscription_path(project_id, subscription_name)
        
    def start_consuming(self, callback: Callable[[ProcessingTask], None]) -> None:
        """Start consuming messages from Pub/Sub subscription"""
        logger.info(f"Starting to consume messages from {self._subscription_path}")
        
        flow_control = pubsub_v1.types.FlowControl(max_messages=1)  # Process one task at a time
        
        def message_handler(message):
            try:
                logger.info(f"Received message: {message.message_id}")
                
                # Parse task data
                task_data = json.loads(message.data.decode('utf-8'))
                task = ProcessingTask(
                    task_id=UUID(task_data["task_id"]),
                    image_path=task_data["image_path"],
                )
                
                # Process task
                callback(task)
                
                # Acknowledge message after successful processing
                message.ack()
                logger.info(f"Successfully processed task {task.task_id}")
                
            except Exception as e:
                logger.error(f"Failed to process message {message.message_id}: {e}")
                # Nack the message to retry on another worker
                message.nack()
        
        # Start pulling messages
        streaming_pull_future = self._subscriber.subscribe(
            self._subscription_path,
            callback=message_handler,
            flow_control=flow_control
        )
        
        logger.info(f"Listening for messages on {self._subscription_path}...")
        
        try:
            streaming_pull_future.result()  # Block indefinitely
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("Stopped consuming messages")
        except Exception as e:
            streaming_pull_future.cancel()
            logger.error(f"Error in message consumption: {e}")
            raise