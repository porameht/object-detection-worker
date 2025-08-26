import json
import io
from PIL import Image
from google.cloud import storage
from google.cloud.exceptions import NotFound

from src.domain.repositories.image_repository import ImageRepository


class GCSImageRepository(ImageRepository):
    def __init__(self, client: storage.Client, bucket_name: str):
        self._client = client
        self._bucket_name = bucket_name
        self._bucket = self._client.bucket(bucket_name)

    async def retrieve_image(self, key: str) -> Image.Image:
        try:
            blob = self._bucket.blob(key)
            image_data = blob.download_as_bytes()
            return Image.open(io.BytesIO(image_data)).convert('RGB')
        except NotFound:
            raise RuntimeError(f"Image not found: {key}")
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve image: {e}")

    async def store_results(self, key: str, data: dict) -> None:
        try:
            blob = self._bucket.blob(key)
            blob.upload_from_string(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
        except Exception as e:
            raise RuntimeError(f"Failed to store results: {e}")