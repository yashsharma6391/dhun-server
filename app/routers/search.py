from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from app.mongodb import (
    get_songs_collection,
    get_granted_access_collection,
    get_channels_collection
)
from app.schemas.search import SearchResultResponse
from app.routers.songs import mongo_to_response, get_user_like_status
from app.middleware.auth_middleware import get_optional_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])

@router.get("", response_model=SearchResultResponse)
async def search(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_optional_user)
):
    col = get_songs_collection()
    user_id = current_user.id if current_user else None

    songs = []
    async for song in col.find({
        "is_active": True,
        "$or": [
            {"title": {"$regex": q, "$options": "i"}},
            {"artist": {"$regex": q, "$options": "i"}},
            {"album": {"$regex": q, "$options": "i"}}
        ]
    }).limit(limit):
        channel_id = song.get("channel_id")
        has_access = True

        if channel_id:
            # FIXED: Check access using MongoDB
            channels_col = get_channels_collection()
            channel = await channels_col.find_one({"id": channel_id})

            if channel and not channel.get("is_public", True):
                if not user_id:
                    has_access = False
                elif user_id != channel.get("owner_id"):
                    access_col = get_granted_access_collection()
                    granted = await access_col.find_one({
                        "channel_id": channel_id,
                        "user_id": user_id,
                        "status": "granted"
                    })
                    has_access = granted is not None

        like_status = await get_user_like_status(song.get("id", ""), user_id)
        songs.append(mongo_to_response(song, like_status, has_access))

    logger.debug(f"Search '{q}': {len(songs)} results")
    return SearchResultResponse(songs=songs, channels=[])

@router.get("/online", response_model=SearchResultResponse)
async def search_online(
    q: str = Query(..., min_length=1),
    current_user: Optional[User] = Depends(get_optional_user)
):
    return await search(q=q, current_user=current_user)