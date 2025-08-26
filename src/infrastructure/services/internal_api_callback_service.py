import requests
import logging
from datetime import datetime, UTC

from src.domain.entities.detection_result import ProcessingResult
from src.domain.entities.serializers import serialize_processing_result
from src.domain.repositories.callback_service import CallbackService

logger = logging.getLogger(__name__)


class InternalAPICallbackService(CallbackService):
    def __init__(self, api_service_url: str, timeout: int = 30):
        self._api_service_url = api_service_url.rstrip('/')
        self._timeout = timeout

    async def send_callback(self, result: ProcessingResult) -> None:
        """Send result via internal API call"""
        
        # Prepare result payload using shared serializer (DRY)
        results_data = serialize_processing_result(result)
        payload = {
            "task_id": str(result.task_id),
            "status": "completed",
            "results": {
                "detection_count": len(result.detections),
                **results_data,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
        
        # Send to internal API
        try:
            url = f"{self._api_service_url}/internal/task-completed"
            logger.info(f"Sending callback for task {result.task_id}")
            
            response = requests.post(url, json=payload, timeout=self._timeout)
            response.raise_for_status()
            logger.info(f"Callback sent successfully for task {result.task_id}")
            
        except Exception as e:
            logger.error(f"Callback failed for task {result.task_id}: {e}")
        
