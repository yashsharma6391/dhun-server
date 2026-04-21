import uuid
import io
import logging
from app.storage.base import BaseStorage, StorageResult
from app.config import settings

logger = logging.getLogger(__name__)

class GDriveStorage(BaseStorage):

    def __init__(self):
        self._initialized = False
        self._service = None

    def initialize(self):
        if self._initialized:
            return
        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_CREDENTIALS_FILE,
                scopes=["https://www.googleapis.com/auth/drive"]
            )
            self._service = build("drive", "v3", credentials=creds)
            self._initialized = True
            logger.info("Google Drive initialized ✅")
        except Exception as e:
            logger.error(f"GDrive init error: {e}")
            raise

    async def upload_audio(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "audio/mpeg"
    ) -> StorageResult:
        return await self._upload(
            file_content=file_content,
            filename=f"{uuid.uuid4()}.mp3",
            mimetype=content_type,
            folder_id=settings.GDRIVE_AUDIO_FOLDER_ID
        )

    async def upload_cover(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> StorageResult:
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
        return await self._upload(
            file_content=file_content,
            filename=f"{uuid.uuid4()}.{ext}",
            mimetype=content_type,
            folder_id=settings.GDRIVE_COVERS_FOLDER_ID
        )

    async def upload_lyrics(
        self,
        file_content: bytes,
        filename: str
    ) -> StorageResult:
        return await self._upload(
            file_content=file_content,
            filename=f"{uuid.uuid4()}.txt",
            mimetype="text/plain",
            folder_id=settings.GDRIVE_LYRICS_FOLDER_ID
        )

    async def _upload(
        self,
        file_content: bytes,
        filename: str,
        mimetype: str,
        folder_id: str
    ) -> StorageResult:
        self.initialize()
        try:
            from googleapiclient.http import MediaIoBaseUpload
            metadata = {"name": filename, "parents": [folder_id]}
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mimetype,
                resumable=True
            )
            file = self._service.files().create(
                body=metadata,
                media_body=media,
                fields="id"
            ).execute()

            file_id = file["id"]

            # Make public
            self._service.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"}
            ).execute()

            url = f"https://drive.google.com/uc?export=view&id={file_id}"
            logger.info(f"Uploaded to GDrive: {filename}")

            return StorageResult(
                public_url=url,
                file_id=file_id,
                provider="gdrive"
            )
        except Exception as e:
            logger.error(f"GDrive upload error: {e}")
            raise

    async def delete_file(self, file_id: str) -> bool:
        self.initialize()
        try:
            self._service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted from GDrive: {file_id}")
            return True
        except Exception as e:
            logger.warning(f"GDrive delete error: {e}")
            return False

    def get_provider_name(self) -> str:
        return "gdrive"