from abc import ABC, abstractmethod

from ..entities.detection_result import ProcessingResult


class CallbackService(ABC):
    @abstractmethod
    async def send_callback(self, result: ProcessingResult) -> None:
        pass