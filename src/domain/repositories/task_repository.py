from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.detection_result import ProcessingResult


class TaskRepository(ABC):
    @abstractmethod
    async def update_task_status(self, task_id: UUID, status: str, result: ProcessingResult = None) -> None:
        pass