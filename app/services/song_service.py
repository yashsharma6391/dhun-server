from sqlalchemy.orm import Session
from app.models.song import Song
from app.models.channel import Channel
from app.schemas.song import SongResponse
from typing import List
import time

def get_trending_songs(
    db: Session,
    page: int = 1,
    limit: int = 20
) -> List[SongResponse]:
    offset = (page - 1) * limit
    songs = db.query(Song)\
        .filter(Song.is_active == True)\
        .order_by(Song.play_count.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    return [song_to_response(s) for s in songs]

def get_song_by_id(song_id: str, db: Session) -> SongResponse:
    song = db.query(Song).filter(
        Song.id == song_id,
        Song.is_active == True
    ).first()
    
    if not song:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found"
        )
    
    # Increment play count
    song.play_count += 1
    db.commit()
    
    return song_to_response(song)

def get_songs_by_channel(
    channel_id: str,
    db: Session,
    page: int = 1,
    limit: int = 20
) -> List[SongResponse]:
    offset = (page - 1) * limit
    songs = db.query(Song)\
        .filter(
            Song.channel_id == channel_id,
            Song.is_active == True
        )\
        .order_by(Song.uploaded_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    return [song_to_response(s) for s in songs]

def song_to_response(song: Song) -> SongResponse:
    channel_name = None
    try:
        channel_name = song.channel.name if song.channel else None
    except Exception:
        pass

    return SongResponse(
        id=song.id,
        title=song.title,
        artist=song.artist,
        album=song.album or "",
        duration=song.duration or 0,
        cover_url=song.cover_url,
        audio_url=song.audio_url,
        # FIXED: Added lyrics_url
        lyrics_url=song.lyrics_url,
        channel_id=song.channel_id,
        channel_name=channel_name,
        uploaded_at=int(song.uploaded_at.timestamp() * 1000) if song.uploaded_at else 0,
        play_count=song.play_count or 0,
        file_size=song.file_size or 0
    )