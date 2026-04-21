from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from app.mongodb import (
    get_songs_collection,
    get_likes_collection,
    get_granted_access_collection
)
from app.schemas.song import SongResponse
from app.middleware.auth_middleware import get_current_user, get_optional_user
from app.models.user import User
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.channel import Channel
import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/songs", tags=["Songs"])

async def get_user_like_status(
    song_id: str,
    user_id: Optional[str]
) -> dict:
    """Get like/dislike status for a user on a song"""
    if not user_id:
        return {"liked": False, "disliked": False}
    likes_col = get_likes_collection()
    existing = await likes_col.find_one({
        "song_id": song_id,
        "user_id": user_id
    })
    if not existing:
        return {"liked": False, "disliked": False}
    return {
        "liked": existing.get("type") == "like",
        "disliked": existing.get("type") == "dislike"
    }

async def check_song_access(
    song: dict,
    user_id: Optional[str],
    db: Session
) -> bool:
    """
    Check if user can access this song
    Public channel songs → everyone can access
    Private channel songs → only owner + granted users
    """
    channel_id = song.get("channel_id")
    if not channel_id:
        return True

    # Get channel from SQLite
    channel = db.query(Channel).filter(
        Channel.id == channel_id
    ).first()

    if not channel:
        return True

    # Public channel → everyone can access
    if channel.is_public:
        return True

    # Private channel
    if not user_id:
        return False

    # Owner always has access
    if channel.owner_id == user_id:
        return True

    # Check granted access
    access_col = get_granted_access_collection()
    granted = await access_col.find_one({
        "channel_id": channel_id,
        "user_id": user_id,
        "status": "granted"
    })
    return granted is not None

def mongo_to_response(
    song: dict,
    like_status: dict = None,
    has_access: bool = True
) -> SongResponse:
    uploaded_at = song.get("uploaded_at")
    uploaded_at_ms = int(uploaded_at.timestamp() * 1000) \
        if hasattr(uploaded_at, "timestamp") else 0

    like_status = like_status or {"liked": False, "disliked": False}

    # If no access - hide audio URL
    audio_url = song.get("audio_url", "") if has_access else ""

    return SongResponse(
        id=song.get("id", str(song.get("_id", ""))),
        title=song.get("title", ""),
        artist=song.get("artist", ""),
        album=song.get("album", ""),
        duration=song.get("duration", 0),
        cover_url=song.get("cover_url"),
        audio_url=audio_url,
        lyrics_url=song.get("lyrics_url") if has_access else None,
        channel_id=song.get("channel_id"),
        channel_name=song.get("channel_name"),
        uploaded_at=uploaded_at_ms,
        play_count=song.get("play_count", 0),
        file_size=song.get("file_size", 0),
        like_count=song.get("like_count", 0),
        dislike_count=song.get("dislike_count", 0),
        user_liked=like_status["liked"],
        user_disliked=like_status["disliked"]
    )

@router.get("/trending", response_model=List[SongResponse])
async def trending_songs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    col = get_songs_collection()
    skip = (page - 1) * limit
    user_id = current_user.id if current_user else None

    # FIXED: Smart trending score calculation
    # Score = (play_count * 1) + (like_count * 3) - (dislike_count * 2)
    # Higher likes = higher rank
    # Recent songs get boost
    
    pipeline = [
        {"$match": {"is_active": True}},
        {"$addFields": {
            "trending_score": {
                "$add": [
                    {"$multiply": [{"$ifNull": ["$play_count", 0]}, 1]},
                    {"$multiply": [{"$ifNull": ["$like_count", 0]}, 3]},
                    {"$multiply": [
                        {"$ifNull": ["$dislike_count", 0]}, -2
                    ]}
                ]
            }
        }},
        {"$sort": {"trending_score": -1, "uploaded_at": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ]

    songs = []
    async for song in col.aggregate(pipeline):
        has_access = await check_song_access(song, user_id, db)
        like_status = await get_user_like_status(
            song.get("id", ""), user_id
        )
        songs.append(mongo_to_response(song, like_status, has_access))

    logger.debug(f"Trending: {len(songs)} songs (smart score)")
    return songs
@router.get("/recent", response_model=List[SongResponse])
async def recent_songs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    col = get_songs_collection()
    skip = (page - 1) * limit
    user_id = current_user.id if current_user else None

    songs = []
    async for song in col.find(
        {"is_active": True}
    ).sort("uploaded_at", -1).skip(skip).limit(limit):
        has_access = await check_song_access(song, user_id, db)
        like_status = await get_user_like_status(
            song.get("id", ""), user_id
        )
        songs.append(mongo_to_response(song, like_status, has_access))

    return songs

@router.get("/channel/{channel_id}", response_model=List[SongResponse])
async def songs_by_channel(
    channel_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    col = get_songs_collection()
    skip = (page - 1) * limit
    user_id = current_user.id if current_user else None

    songs = []
    async for song in col.find(
        {"channel_id": channel_id, "is_active": True}
    ).sort("uploaded_at", -1).skip(skip).limit(limit):
        has_access = await check_song_access(song, user_id, db)
        like_status = await get_user_like_status(
            song.get("id", ""), user_id
        )
        songs.append(mongo_to_response(song, like_status, has_access))

    return songs

@router.get("/{song_id}", response_model=SongResponse)
async def song_by_id(
    song_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    col = get_songs_collection()
    song = await col.find_one({"id": song_id})
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    user_id = current_user.id if current_user else None
    has_access = await check_song_access(song, user_id, db)
    like_status = await get_user_like_status(song_id, user_id)

    await col.update_one(
        {"id": song_id},
        {"$inc": {"play_count": 1}}
    )

    return mongo_to_response(song, like_status, has_access)

# ─── LIKE / DISLIKE ───────────────────────────────────────

@router.post("/{song_id}/like")
async def like_song(
    song_id: str,
    current_user: User = Depends(get_current_user)
):
    songs_col = get_songs_collection()
    likes_col = get_likes_collection()

    song = await songs_col.find_one({"id": song_id})
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    existing = await likes_col.find_one({
        "song_id": song_id,
        "user_id": current_user.id
    })

    if existing:
        if existing["type"] == "like":
            # Unlike - remove like
            await likes_col.delete_one({"_id": existing["_id"]})
            await songs_col.update_one(
                {"id": song_id},
                {"$inc": {"like_count": -1}}
            )
            return {"action": "unliked", "song_id": song_id}
        else:
            # Was dislike - switch to like
            await likes_col.update_one(
                {"_id": existing["_id"]},
                {"$set": {"type": "like"}}
            )
            await songs_col.update_one(
                {"id": song_id},
                {"$inc": {"like_count": 1, "dislike_count": -1}}
            )
            return {"action": "liked", "song_id": song_id}
    else:
        # New like
        await likes_col.insert_one({
            "song_id": song_id,
            "user_id": current_user.id,
            "type": "like",
            "created_at": datetime.datetime.utcnow()
        })
        await songs_col.update_one(
            {"id": song_id},
            {"$inc": {"like_count": 1}}
        )
        return {"action": "liked", "song_id": song_id}

@router.post("/{song_id}/dislike")
async def dislike_song(
    song_id: str,
    current_user: User = Depends(get_current_user)
):
    songs_col = get_songs_collection()
    likes_col = get_likes_collection()

    song = await songs_col.find_one({"id": song_id})
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    existing = await likes_col.find_one({
        "song_id": song_id,
        "user_id": current_user.id
    })

    if existing:
        if existing["type"] == "dislike":
            # Un-dislike
            await likes_col.delete_one({"_id": existing["_id"]})
            await songs_col.update_one(
                {"id": song_id},
                {"$inc": {"dislike_count": -1}}
            )
            return {"action": "undisliked", "song_id": song_id}
        else:
            # Was like - switch to dislike
            await likes_col.update_one(
                {"_id": existing["_id"]},
                {"$set": {"type": "dislike"}}
            )
            await songs_col.update_one(
                {"id": song_id},
                {"$inc": {"like_count": -1, "dislike_count": 1}}
            )
            return {"action": "disliked", "song_id": song_id}
    else:
        # New dislike
        await likes_col.insert_one({
            "song_id": song_id,
            "user_id": current_user.id,
            "type": "dislike",
            "created_at": datetime.datetime.utcnow()
        })
        await songs_col.update_one(
            {"id": song_id},
            {"$inc": {"dislike_count": 1}}
        )
        return {"action": "disliked", "song_id": song_id}
    
@router.delete("/{song_id}")
async def delete_song_by_id(
    song_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a song (owner only)"""
    songs_col = get_songs_collection()
    song = await songs_col.find_one({"id": song_id})

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # Check ownership via channel
    channel_id = song.get("channel_id")
    if channel_id:
        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.owner_id == current_user.id
        ).first()
        if not channel:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to delete this song"
            )

    await songs_col.update_one(
        {"id": song_id},
        {"$set": {"is_active": False}}
    )

    logger.info(f"Song deleted: {song_id}")
    return {"success": True, "message": "Song deleted"}    