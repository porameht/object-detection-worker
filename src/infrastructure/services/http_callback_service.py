import requests
from datetime import datetime

from ...domain.entities.detection_result import ProcessingResult
from ...domain.repositories.callback_service import CallbackService


class HttpCallbackService(CallbackService):
    def __init__(self, timeout: int = 30):
        self._timeout = timeout

    async def send_callback(self, callback_url: str, result: ProcessingResult) -> None:
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
        
        response = requests.post(callback_url, json=payload, timeout=self._timeout)
        response.raise_for_status()