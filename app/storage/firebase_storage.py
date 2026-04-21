import uuid
import logging
import io
from app.storage.base import BaseStorage, StorageResult
from app.config import settings

logger = logging.getLogger(__name__)

class FirebaseStorage(BaseStorage):

    def __init__(self):
        self._initialized = False
        self._bucket = None

    def initialize(self):
        if self._initialized:
            return
        try:
            import firebase_admin
            from firebase_admin import credentials, storage
            cred = credentials.Certificate(
                settings.FIREBASE_CREDENTIALS_FILE
            )
            firebase_admin.initialize_app(cred, {
                "storageBucket": settings.FIREBASE_STORAGE_BUCKET
            })
            self._bucket = storage.bucket()
            self._initialized = True
            logger.info("Firebase Storage initialized ✅")
        except Exception as e:
            logger.error(f"Firebase init error: {e}")
            raise

    async def upload_audio(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "audio/mpeg"
    ) -> StorageResult:
        return await self._upload(
            file_content, f"audio/{uuid.uuid4()}.mp3", content_type
        )

    async def upload_cover(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> StorageResult:
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
        return await self._upload(
            file_content, f"covers/{uuid.uuid4()}.{ext}", content_type
        )

    async def upload_lyrics(
        self,
        file_content: bytes,
        filename: str
    ) -> StorageResult:
        return await self._upload(
            file_content, f"lyrics/{uuid.uuid4()}.txt", "text/plain"
        )

    async def _upload(
        self,
        file_content: bytes,
        blob_path: str,
        content_type: str
    ) -> StorageResult:
        self.initialize()
        try:
            blob = self._bucket.blob(blob_path)
            blob.upload_from_string(file_content, content_type=content_type)
            blob.make_public()
            url = blob.public_url
            logger.info(f"Uploaded to Firebase: {blob_path}")
            return StorageResult(
                public_url=url,
                file_id=blob_path,
                provider="firebase"
            )
        except Exception as e:
            logger.error(f"Firebase upload error: {e}")
            raise

    async def delete_file(self, file_id: str) -> bool:
        self.initialize()
        try:
            blob = self._bucket.blob(file_id)
            blob.delete()
            logger.info(f"Deleted from Firebase: {file_id}")
            return True
        except Exception as e:
            logger.warning(f"Firebase delete error: {e}")
            return False

    def get_provider_name(self) -> str:
        return "firebase"