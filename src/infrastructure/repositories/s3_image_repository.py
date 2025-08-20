import json
import io
from PIL import Image
import boto3

from ...domain.repositories.image_repository import ImageRepository


class S3ImageRepository(ImageRepository):
    def __init__(self, s3_client: boto3.client, bucket_name: str):
        self._s3 = s3_client
        self._bucket = bucket_name

    async def retrieve_image(self, key: str) -> Image.Image:
        response = self._s3.get_object(Bucket=self._bucket, Key=key)
        image_data = response['Body'].read()
        return Image.open(io.BytesIO(image_data)).convert('RGB')

    async def store_results(self, key: str, data: dict) -> None:
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json',
        )