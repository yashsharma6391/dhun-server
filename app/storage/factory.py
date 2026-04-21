from app.storage.base import BaseStorage
from app.config import settings
import logging

logger = logging.getLogger(__name__)

_storage_instance: BaseStorage = None

def get_storage() -> BaseStorage:
    """
    Returns storage provider based on STORAGE_PROVIDER in .env
    Change .env → STORAGE_PROVIDER=cloudinary|firebase|gdrive
    No code change needed!
    """
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    provider = settings.STORAGE_PROVIDER.lower().strip()
    logger.info(f"Storage provider: {provider}")

    if provider == "cloudinary":
        from app.storage.cloudinary_storage import CloudinaryStorage
        _storage_instance = CloudinaryStorage()

    elif provider == "firebase":
        from app.storage.firebase_storage import FirebaseStorage
        _storage_instance = FirebaseStorage()

    elif provider == "gdrive":
        from app.storage.gdrive_storage import GDriveStorage
        _storage_instance = GDriveStorage()

    else:
        logger.warning(
            f"Unknown provider '{provider}' - defaulting to cloudinary"
        )
        from app.storage.cloudinary_storage import CloudinaryStorage
        _storage_instance = CloudinaryStorage()

    logger.info(f"Using storage: {_storage_instance.get_provider_name()}")
    return _storage_instance