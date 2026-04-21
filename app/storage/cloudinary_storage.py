import cloudinary
import cloudinary.uploader
import cloudinary.api
import uuid
import logging
from app.storage.base import BaseStorage, StorageResult
from app.config import settings

logger = logging.getLogger(__name__)

class CloudinaryStorage(BaseStorage):

    def __init__(self):
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        self._initialized = True
        logger.info("Cloudinary initialized ✅")

    async def upload_audio(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "audio/mpeg"
    ) -> StorageResult:
        self.initialize()
        try:
            public_id = f"dhun/audio/{uuid.uuid4()}"
            result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type="video",  # Cloudinary uses video for audio
                folder="dhun/audio",
                overwrite=True
            )
            url = result["secure_url"]
            file_id = result["public_id"]
            logger.info(f"Audio uploaded to Cloudinary: {url}")
            return StorageResult(
                public_url=url,
                file_id=file_id,
                provider="cloudinary"
            )
        except Exception as e:
            logger.error(f"Cloudinary audio upload error: {e}")
            raise

    async def upload_cover(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> StorageResult:
        self.initialize()
        try:
            public_id = f"dhun/covers/{uuid.uuid4()}"
            result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type="image",
                folder="dhun/covers",
                transformation=[
                    # Auto optimize + resize to 500x500
                    {"width": 500, "height": 500, "crop": "fill"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
            url = result["secure_url"]
            file_id = result["public_id"]
            logger.info(f"Cover uploaded to Cloudinary: {url}")
            return StorageResult(
                public_url=url,
                file_id=file_id,
                provider="cloudinary"
            )
        except Exception as e:
            logger.error(f"Cloudinary cover upload error: {e}")
            raise

    async def upload_lyrics(
        self,
        file_content: bytes,
        filename: str
    ) -> StorageResult:
        self.initialize()
        try:
            public_id = f"dhun/lyrics/{uuid.uuid4()}"
            result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type="raw",  # raw = any file type
                folder="dhun/lyrics"
            )
            url = result["secure_url"]
            file_id = result["public_id"]
            logger.info(f"Lyrics uploaded to Cloudinary: {url}")
            return StorageResult(
                public_url=url,
                file_id=file_id,
                provider="cloudinary"
            )
        except Exception as e:
            logger.error(f"Cloudinary lyrics upload error: {e}")
            raise

    async def delete_file(self, file_id: str) -> bool:
     self.initialize()
     if not file_id:
        return True
     try:
        # FIXED: Detect resource type from file_id path
        # dhun/audio/... → resource_type = "video" (Cloudinary uses video for audio)
        # dhun/covers/... → resource_type = "image"
        # dhun/lyrics/... → resource_type = "raw"
        if "audio" in file_id:
            resource_type = "video"
        elif "covers" in file_id:
            resource_type = "image"
        elif "lyrics" in file_id:
            resource_type = "raw"
        else:
            resource_type = "raw"

        result = cloudinary.uploader.destroy(
            file_id,
            resource_type=resource_type
        )
        logger.info(f"Deleted from Cloudinary: {file_id} result:{result}")
        return True
     except Exception as e:
        logger.warning(f"Cloudinary delete error: {e}")
        return False

    def get_provider_name(self) -> str:
        return "cloudinary"