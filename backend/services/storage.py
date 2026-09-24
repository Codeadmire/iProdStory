"""
Pluggable storage backend.

- LocalStorageBackend:  saves files to disk (dev / single-node)
- S3StorageBackend:     saves to S3-compatible object storage (production)

Both expose the same interface:
    save(data: bytes, key: str, content_type: str) -> str   # returns public URL
    get_url(key: str) -> str
    delete(key: str) -> None
"""
import os
import io
from abc import ABC, abstractmethod
from config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
        ...

    @abstractmethod
    def get_url(self, key: str) -> str:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str, base_url: str):
        self.base_path = base_path
        self.base_url = base_url.rstrip("/")
        os.makedirs(base_path, exist_ok=True)

    def save(self, data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
        full_path = os.path.join(self.base_path, key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        return self.get_url(key)

    def get_url(self, key: str) -> str:
        return f"{self.base_url}/{key}"

    def delete(self, key: str) -> None:
        full_path = os.path.join(self.base_path, key)
        if os.path.exists(full_path):
            os.remove(full_path)


class S3StorageBackend(StorageBackend):
    def __init__(self, bucket: str, region: str, endpoint_url: str = None,
                 aws_key: str = None, aws_secret: str = None):
        import boto3
        self.bucket = bucket
        self.region = region

        kwargs = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        if aws_key and aws_secret:
            kwargs["aws_access_key_id"] = aws_key
            kwargs["aws_secret_access_key"] = aws_secret

        self.client = boto3.client("s3", region_name=region, **kwargs)
        self._endpoint = endpoint_url

    def save(self, data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return self.get_url(key)

    def get_url(self, key: str) -> str:
        if self._endpoint:
            return f"{self._endpoint}/{self.bucket}/{key}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


def get_storage() -> StorageBackend:
    """Factory — returns the configured backend as a singleton."""
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageBackend(
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            aws_key=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret=settings.AWS_SECRET_ACCESS_KEY or None,
        )
    return LocalStorageBackend(
        base_path=settings.LOCAL_STORAGE_PATH,
        base_url=settings.MEDIA_BASE_URL,
    )


# Module-level singleton
storage = get_storage()
