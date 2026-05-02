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
            file_uuid = str(uuid.uuid4())
            # FIXED: Use ONLY public_id, no folder param
            # This prevents duplicate path like dhun/audio/dhun/audio/...
            public_id = f"dhun/audio/{file_uuid}"
            result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type="video",
                overwrite=True
                # FIXED: Removed folder param - public_id already has path
            )
            url = result["secure_url"]
            file_id = result["public_id"]
            logger.info(f"Audio uploaded: {file_id}")
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
            file_uuid = str(uuid.uuid4())
            # FIXED: No folder param
            public_id = f"dhun/covers/{file_uuid}"
            result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type="image",
                overwrite=True,
                transformation=[
                    {"width": 500, "height": 500, "crop": "fill"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
            url = result["secure_url"]
            file_id = result["public_id"]
            logger.info(f"Cover uploaded: {file_id}")
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
            file_uuid = str(uuid.uuid4())
            # FIXED: No folder param
            public_id = f"dhun/lyrics/{file_uuid}"
            result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type="raw",
                overwrite=True
            )
            url = result["secure_url"]
            file_id = result["public_id"]
            logger.info(f"Lyrics uploaded: {file_id}")
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
            # FIXED: Detect resource type correctly
            # file_id examples:
            # dhun/audio/dhun/audio/uuid → video
            # dhun/audio/uuid            → video
            # dhun/covers/uuid           → image
            # dhun/lyrics/uuid           → raw
            file_id_lower = file_id.lower()
            if "audio" in file_id_lower:
                resource_type = "video"
            elif "cover" in file_id_lower:
                resource_type = "image"
            elif "lyrics" in file_id_lower:
                resource_type = "raw"
            else:
                resource_type = "raw"

            logger.info(
                f"Deleting from Cloudinary: {file_id} "
                f"resource_type={resource_type}"
            )
            result = cloudinary.uploader.destroy(
                file_id,
                resource_type=resource_type
            )
            logger.info(f"Delete result: {result}")

            # result = {"result": "ok"} on success
            # result = {"result": "not found"} if not exists
            if result.get("result") == "ok":
                return True
            elif result.get("result") == "not found":
                logger.warning(f"File not found on Cloudinary: {file_id}")
                return True  # Already gone - treat as success
            else:
                logger.warning(f"Unexpected delete result: {result}")
                return False
        except Exception as e:
            logger.error(f"Cloudinary delete error: {e}")
            return False

    def get_provider_name(self) -> str:
        return "cloudinary"