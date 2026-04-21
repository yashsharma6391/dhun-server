from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from typing import Optional
import logging
import traceback
import uuid
import datetime

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.storage.factory import get_storage
from app.mongodb import get_songs_collection, get_channels_collection
from app.schemas.song import SongResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/channels", tags=["Upload"])

@router.post("/{channel_id}/upload", response_model=SongResponse)
async def upload_song(
    channel_id: str,
    title: str = Form(...),
    artist: str = Form(...),
    album: str = Form(""),
    audio_file: UploadFile = File(...),
    cover_file: Optional[UploadFile] = File(default=None),
    lyrics_file: Optional[UploadFile] = File(default=None),
    current_user: User = Depends(get_current_user)
):
    logger.info(
        f"Upload - channel:{channel_id} "
        f"title:{title} user:{current_user.email}"
    )

    try:
        # Verify channel ownership using MongoDB
        channels_col = get_channels_collection()
        channel = await channels_col.find_one({
            "id": channel_id,
            "owner_id": current_user.id
        })

        if not channel:
            raise HTTPException(
                status_code=403,
                detail="Channel not found or not yours"
            )

        storage = get_storage()
        song_id = str(uuid.uuid4())

        # Upload audio
        logger.info(f"Uploading audio via {storage.get_provider_name()}...")
        audio_content = await audio_file.read()
        if not audio_content:
            raise HTTPException(status_code=400, detail="Audio file empty")

        audio_result = await storage.upload_audio(
            file_content=audio_content,
            filename=audio_file.filename or "audio.mp3",
            content_type=audio_file.content_type or "audio/mpeg"
        )
        logger.info(f"Audio uploaded: {audio_result.public_url}")

        # Upload cover (optional)
        cover_url = None
        cover_file_id = None
        if cover_file and cover_file.filename:
            cover_content = await cover_file.read()
            if cover_content:
                cover_result = await storage.upload_cover(
                    file_content=cover_content,
                    filename=cover_file.filename,
                    content_type=cover_file.content_type or "image/jpeg"
                )
                cover_url = cover_result.public_url
                cover_file_id = cover_result.file_id

        # Upload lyrics (optional)
        lyrics_url = None
        lyrics_file_id = None
        if lyrics_file and lyrics_file.filename:
            lyrics_content = await lyrics_file.read()
            if lyrics_content:
                lyrics_result = await storage.upload_lyrics(
                    file_content=lyrics_content,
                    filename=lyrics_file.filename
                )
                lyrics_url = lyrics_result.public_url
                lyrics_file_id = lyrics_result.file_id

        # Save to MongoDB
        songs_col = get_songs_collection()
        now = datetime.datetime.utcnow()

        song_doc = {
            "_id": song_id,
            "id": song_id,
            "title": title,
            "artist": artist,
            "album": album,
            "audio_url": audio_result.public_url,
            "cover_url": cover_url,
            "lyrics_url": lyrics_url,
            "duration": 0,
            "file_size": len(audio_content),
            "play_count": 0,
            "like_count": 0,
            "dislike_count": 0,
            "channel_id": channel_id,
            "channel_name": channel.get("name", ""),
            "uploaded_by": current_user.id,
            "is_active": True,
            "uploaded_at": now,
            "storage_provider": storage.get_provider_name(),
            "audio_file_id": audio_result.file_id,
            "cover_file_id": cover_file_id,
            "lyrics_file_id": lyrics_file_id
        }

        await songs_col.insert_one(song_doc)
        logger.info(f"Song saved: {song_id}")

        return SongResponse(
            id=song_id,
            title=title,
            artist=artist,
            album=album,
            duration=0,
            cover_url=cover_url,
            audio_url=audio_result.public_url,
            lyrics_url=lyrics_url,
            channel_id=channel_id,
            channel_name=channel.get("name", ""),
            uploaded_at=int(now.timestamp() * 1000),
            play_count=0,
            file_size=len(audio_content)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload ERROR: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))