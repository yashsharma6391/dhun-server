from abc import ABC, abstractmethod
from typing import Optional

class StorageResult:
    """Returned after every upload"""
    def __init__(
        self,
        public_url: str,
        file_id: str,
        provider: str
    ):
        self.public_url = public_url
        self.file_id = file_id       # Used for deletion
        self.provider = provider

    def __repr__(self):
        return f"<StorageResult url={self.public_url} provider={self.provider}>"


class BaseStorage(ABC):
    """
    All storage providers implement this.
    To add new provider - just implement these 4 methods.
    """

    @abstractmethod
    async def upload_audio(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "audio/mpeg"
    ) -> StorageResult:
        pass

    @abstractmethod
    async def upload_cover(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> StorageResult:
        pass

    @abstractmethod
    async def upload_lyrics(
        self,
        file_content: bytes,
        filename: str
    ) -> StorageResult:
        pass

    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass