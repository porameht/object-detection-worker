import requests
import logging
from datetime import datetime

from ...domain.entities.detection_result import ProcessingResult
from ...domain.repositories.callback_service import CallbackService

logger = logging.getLogger(__name__)


class InternalAPICallbackService(CallbackService):
    def __init__(self, api_service_url: str, timeout: int = 30):
        self._api_service_url = api_service_url.rstrip('/')
        self._timeout = timeout

    async def send_callback(self, result: ProcessingResult) -> None:
        """Send result via internal API call"""
        
        # Prepare result payload
        payload = {
            "task_id": str(result.task_id),
            "status": "completed",
            "results": {
                "detection_count": len(result.detections),
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
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Send to internal API for long polling notification
        try:
            internal_url = f"{self._api_service_url}/internal/task-completed"
            logger.info(f"[CALLBACK] Sending task completion to API: {internal_url}")
            logger.info(f"[CALLBACK] Task ID: {result.task_id}, Detections: {len(result.detections)}, Processing time: {result.processing_time_ms}ms")
            
            response = requests.post(internal_url, json=payload, timeout=self._timeout)
            response.raise_for_status()
            
            logger.info(f"[CALLBACK] ✅ Successfully notified API service for task {result.task_id}")
            logger.info(f"[CALLBACK] API Response: Status={response.status_code}")
            
        except Exception as e:
            logger.error(f"[CALLBACK] ❌ Failed to notify API service for task {result.task_id}")
            logger.error(f"[CALLBACK] Error details: {str(e)}")
            # Continue - don't fail the whole process
        
