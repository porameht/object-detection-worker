from abc import ABC, abstractmethod

from ..entities.detection_result import ProcessingResult


class CallbackService(ABC):
    @abstractmethod
    async def send_callback(self, callback_url: str, result: ProcessingResult) -> None:
        pass