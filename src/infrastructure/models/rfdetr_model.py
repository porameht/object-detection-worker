from typing import List
from PIL import Image
import supervision as sv
from rfdetr import RFDETRBase
from rfdetr.util.coco_classes import COCO_CLASSES

from ...domain.entities.detection_result import Detection, BoundingBox
from ...domain.repositories.detection_model import DetectionModel


class RFDETRModel(DetectionModel):
    def __init__(self, confidence_threshold: float = 0.5):
        self._model = RFDETRBase()
        self._coco_classes = COCO_CLASSES
        self._confidence_threshold = confidence_threshold

    def predict(self, image: Image.Image) -> List[Detection]:
        detections_sv = self._model.predict(image)
        
        detections = []
        for class_id, confidence, bbox in zip(
            detections_sv.class_id,
            detections_sv.confidence,
            detections_sv.xyxy,
        ):
            if confidence >= self._confidence_threshold:
                detection = Detection(
                    class_id=int(class_id),
                    class_name=self._coco_classes[int(class_id)],
                    confidence=float(confidence),
                    bbox=BoundingBox(
                        x1=float(bbox[0]),
                        y1=float(bbox[1]),
                        x2=float(bbox[2]),
                        y2=float(bbox[3]),
                    ),
                )
                detections.append(detection)
        
        return detections