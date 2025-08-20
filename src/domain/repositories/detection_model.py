from abc import ABC, abstractmethod
from typing import List
from PIL import Image

from ..entities.detection_result import Detection


class DetectionModel(ABC):
    @abstractmethod
    def predict(self, image: Image.Image) -> List[Detection]:
        pass