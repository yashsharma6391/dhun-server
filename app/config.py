from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # SQLite (users/auth only)
    DATABASE_URL: str = "sqlite:///./dhun.db"

    # MongoDB (songs/channels)
    MONGODB_URL: str = ""
    MONGODB_DB_NAME: str = "dhun_music"

    # Storage provider
    STORAGE_PROVIDER: str = "cloudinary"

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Firebase (optional)
    FIREBASE_CREDENTIALS_FILE: str = "firebase_credentials.json"
    FIREBASE_STORAGE_BUCKET: str = ""

    # Google Drive (optional)
    GOOGLE_CREDENTIALS_FILE: str = "google_credentials.json"
    GDRIVE_AUDIO_FOLDER_ID: str = ""
    GDRIVE_COVERS_FOLDER_ID: str = ""
    GDRIVE_LYRICS_FOLDER_ID: str = ""

    # JWT
    SECRET_KEY: str = "dhun_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    # FIXED: DEBUG=False in production
    DEBUG: bool = False

    # Server base URL
    # Local: http://192.168.x.x:8000
    # Production: https://dhun-server.onrender.com
    SERVER_BASE_URL: str = ""

    # Upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "uploads"
    ALLOWED_AUDIO_TYPES: str = "audio/mpeg,audio/mp3,audio/wav,audio/flac,audio/ogg"

    # CORS
    CORS_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        extra = "allow"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()