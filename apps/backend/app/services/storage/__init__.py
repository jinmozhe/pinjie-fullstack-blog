from app.core.config import Settings

from .base import StagedDeletion, StagedFile, StorageProvider
from .local import LocalStorageProvider


def create_storage_provider(settings: Settings) -> StorageProvider:
    if settings.upload_storage_driver == "local":
        return LocalStorageProvider(settings.upload_local_root, io_concurrency=settings.upload_io_concurrency)
    raise ValueError("unsupported upload storage driver")


__all__ = [
    "create_storage_provider",
    "LocalStorageProvider",
    "StagedDeletion",
    "StagedFile",
    "StorageProvider",
]
