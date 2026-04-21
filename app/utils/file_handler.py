import os
import uuid
import aiofiles
from fastapi import UploadFile
from mutagen import File as MutagenFile
from app.config import settings
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = settings.UPLOAD_DIR
AUDIO_DIR = os.path.join(UPLOAD_DIR, "audio")
COVER_DIR = os.path.join(UPLOAD_DIR, "covers")
# FIXED: Added lyrics directory
LYRICS_DIR = os.path.join(UPLOAD_DIR, "lyrics")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)
os.makedirs(LYRICS_DIR, exist_ok=True)

async def save_audio_file(file: UploadFile) -> dict:
    ext = os.path.splitext(file.filename)[1] or ".mp3"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(AUDIO_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)

    duration = 0
    file_size = len(content)
    try:
        audio = MutagenFile(filepath)
        if audio and audio.info:
            duration = int(audio.info.length * 1000)
    except Exception as e:
        logger.warning(f"Could not read audio duration: {e}")

    base_url = settings.SERVER_BASE_URL
    audio_url = f"{base_url}/uploads/audio/{filename}"
    logger.debug(f"Audio URL: {audio_url}")

    return {
        "filename": filename,
        "filepath": filepath,
        "audio_url": audio_url,
        "duration": duration,
        "file_size": file_size
    }

async def save_cover_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(COVER_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)

    base_url = settings.SERVER_BASE_URL
    cover_url = f"{base_url}/uploads/covers/{filename}"
    logger.debug(f"Cover URL: {cover_url}")
    return cover_url

# FIXED: Added save lyrics file
async def save_lyrics_file(file: UploadFile) -> str:
    filename = f"{uuid.uuid4()}.txt"
    filepath = os.path.join(LYRICS_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)

    base_url = settings.SERVER_BASE_URL
    lyrics_url = f"{base_url}/uploads/lyrics/{filename}"
    logger.debug(f"Lyrics URL: {lyrics_url}")
    return lyrics_url

def delete_file(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass