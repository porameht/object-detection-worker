from abc import ABC, abstractmethod
from PIL import Image


class ImageRepository(ABC):
    @abstractmethod
    async def retrieve_image(self, key: str) -> Image.Image:
        pass

    @abstractmethod
    async def store_results(self, key: str, data: dict) -> None:
        pass