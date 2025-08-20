import redis
import boto3
import json
import logging
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
import supervision as sv
from PIL import Image
from rfdetr import RFDETRBase
from rfdetr.util.coco_classes import COCO_CLASSES
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObjectDetectionWorker:
    def __init__(self):
        # Configuration
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.s3_bucket = os.getenv("S3_BUCKET", "object-detection-images")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.metadata_db_host = os.getenv("METADATA_DB_HOST", "localhost")
        
        # Initialize services
        self.s3_client = boto3.client('s3', region_name=self.aws_region)
        self.redis_client = redis.from_url(self.redis_url)
        
        # Load ML model
        self.model = self._load_model()
        self.coco_classes = COCO_CLASSES
        
        logger.info("Worker initialized successfully")
    
    def _load_model(self):
        """Load the RF-DETR object detection model"""
        try:
            model = RFDETRBase()
            return model
        except Exception as e:
            logger.error(f"Error loading RF-DETR model: {e}")
            raise
    
    def _download_image_from_s3(self, s3_key: str) -> Image.Image:
        """Download image from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            image_data = response['Body'].read()
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            return image
        except Exception as e:
            logger.error(f"Error downloading image from S3: {e}")
            raise
    
    def _detect_objects(self, image: Image.Image) -> List[Dict]:
        """Perform object detection on image using RF-DETR"""
        try:
            # Run RF-DETR inference
            detections = self.model.predict(image)
            
            # Process results
            detection_list = []
            for class_id, confidence, bbox in zip(
                detections.class_id,
                detections.confidence,
                detections.xyxy,
            ):
                if confidence > 0.5:  # Confidence threshold
                    detection_list.append({
                        "class_id": int(class_id),
                        "class_name": self.coco_classes[int(class_id)],
                        "confidence": float(confidence),
                        "bbox": {
                            "x1": float(bbox[0]),
                            "y1": float(bbox[1]),
                            "x2": float(bbox[2]),
                            "y2": float(bbox[3])
                        }
                    })
            
            return detection_list
        except Exception as e:
            logger.error(f"Error during object detection: {e}")
            raise
    
    def _save_results_to_s3(self, task_id: str, results: Dict) -> str:
        """Save detection results to S3"""
        try:
            results_key = f"results/{task_id}/detection_results.json"
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=results_key,
                Body=json.dumps(results, indent=2),
                ContentType='application/json'
            )
            return results_key
        except Exception as e:
            logger.error(f"Error saving results to S3: {e}")
            raise
    
    def _update_task_status(self, task_id: str, status: str, results: Optional[Dict] = None):
        """Update task status in Redis"""
        try:
            task_data = self.redis_client.get(f"task:{task_id}")
            if task_data:
                task_info = json.loads(task_data)
                task_info["status"] = status
                task_info["updated_at"] = datetime.utcnow().isoformat()
                
                if results:
                    task_info["results"] = results
                
                self.redis_client.setex(f"task:{task_id}", 3600, json.dumps(task_info))
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
    
    def _send_callback(self, callback_url: str, task_id: str, results: Dict):
        """Send callback notification"""
        try:
            payload = {
                "task_id": task_id,
                "status": "completed",
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = requests.post(callback_url, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Callback sent successfully for task {task_id}")
        except Exception as e:
            logger.error(f"Error sending callback for task {task_id}: {e}")
    
    def process_task(self, task_data: Dict):
        """Process a single detection task"""
        task_id = task_data["task_id"]
        image_key = task_data["image_key"]
        callback_url = task_data.get("callback_url")
        
        logger.info(f"Processing task {task_id}")
        
        try:
            # Update status to processing
            self._update_task_status(task_id, "processing")
            
            # Download image from S3
            image = self._download_image_from_s3(image_key)
            
            # Perform object detection
            detections = self._detect_objects(image)
            
            # Prepare results
            results = {
                "task_id": task_id,
                "image_key": image_key,
                "detections": detections,
                "detection_count": len(detections),
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # Save results to S3
            results_key = self._save_results_to_s3(task_id, results)
            results["results_key"] = results_key
            
            # Update task status
            self._update_task_status(task_id, "completed", results)
            
            # Send callback if provided
            if callback_url:
                self._send_callback(callback_url, task_id, results)
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            self._update_task_status(task_id, "failed")
    
    def run(self):
        """Main worker loop"""
        logger.info("Starting object detection worker...")
        
        while True:
            try:
                # Block until task available (with timeout)
                task_data = self.redis_client.brpop("detection_queue", timeout=10)
                
                if task_data:
                    queue_name, task_json = task_data
                    task_info = json.loads(task_json)
                    self.process_task(task_info)
                
            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in worker main loop: {e}")
                continue

if __name__ == "__main__":
    worker = ObjectDetectionWorker()
    worker.run()