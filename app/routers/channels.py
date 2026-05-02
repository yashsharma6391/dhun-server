from fastapi import APIRouter, Depends, Body, HTTPException
from typing import List, Optional
import logging
import datetime
import uuid

from app.schemas.channel import ChannelResponse, AccessRequestResponse
from app.middleware.auth_middleware import get_current_user, get_optional_user
from app.models.user import User
from app.models.channel import Channel
from app.mongodb import (
    get_channels_collection,
    get_users_collection,
    get_songs_collection,
    get_follows_collection,
    get_access_requests_collection,
    get_granted_access_collection
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/channels", tags=["Channels"])

async def get_song_count(channel_id: str) -> int:
    try:
        col = get_songs_collection()
        return await col.count_documents(
            {"channel_id": channel_id, "is_active": True}
        )
    except Exception:
        return 0

async def is_following(channel_id: str, user_id: str) -> bool:
    follows_col = get_follows_collection()
    follow = await follows_col.find_one({
        "channel_id": channel_id,
        "user_id": user_id
    })
    return follow is not None

async def get_access_status(
    channel_id: str,
    user_id: Optional[str],
    channel_owner_id: str,
    is_public: bool
) -> str:
    if not user_id:
        return "none"
    if user_id == channel_owner_id:
        return "owner"
    if is_public:
        return "granted"

    access_col = get_granted_access_collection()
    granted = await access_col.find_one({
        "channel_id": channel_id,
        "user_id": user_id,
        "status": "granted"
    })
    if granted:
        return "granted"

    req_col = get_access_requests_collection()
    pending = await req_col.find_one({
        "channel_id": channel_id,
        "user_id": user_id,
        "status": "pending"
    })
    if pending:
        return "pending"

    return "none"

def channel_doc_to_response(
    doc: dict,
    song_count: int = 0,
    is_following_ch: bool = False,
    access_stat: str = "none"
) -> ChannelResponse:
    created_at = doc.get("created_at")
    created_at_ms = int(created_at.timestamp() * 1000) \
        if hasattr(created_at, "timestamp") else 0

    return ChannelResponse(
        id=doc.get("id", str(doc.get("_id", ""))),
        name=doc.get("name", ""),
        description=doc.get("description", ""),
        owner_name=doc.get("owner_name", ""),
        owner_id=doc.get("owner_id", ""),
        cover_url=doc.get("cover_url"),
        song_count=song_count,
        follower_count=doc.get("follower_count", 0),
        created_at=created_at_ms,
        is_public=doc.get("is_public", True),
        is_following=is_following_ch,
        access_status=access_stat
    )

@router.get("/popular", response_model=List[ChannelResponse])
async def popular_channels(
    current_user: Optional[User] = Depends(get_optional_user)
):
    channels_col = get_channels_collection()
    user_id = current_user.id if current_user else None

    query = {}
    if user_id:
        query["owner_id"] = {"$ne": user_id}

    result = []
    async for doc in channels_col.find(query).sort(
        "follower_count", -1
    ).limit(20):
        count = await get_song_count(doc.get("id", ""))
        following = await is_following(doc.get("id", ""), user_id) \
            if user_id else False
        access = await get_access_status(
            doc.get("id", ""), user_id,
            doc.get("owner_id", ""), doc.get("is_public", True)
        ) if user_id else "none"
        result.append(channel_doc_to_response(doc, count, following, access))
    return result

@router.get("/my", response_model=Optional[ChannelResponse])
async def my_channel(
    current_user: User = Depends(get_current_user)
):
    if not current_user.channel_id:
        return None

    channels_col = get_channels_collection()
    doc = await channels_col.find_one({"id": current_user.channel_id})
    if not doc:
        # Try by owner_id
        doc = await channels_col.find_one({"owner_id": current_user.id})
    if not doc:
        return None

    count = await get_song_count(doc.get("id", ""))
    return channel_doc_to_response(doc, count, False, "owner")

@router.get("/following", response_model=List[ChannelResponse])
async def followed_channels(
    current_user: User = Depends(get_current_user)
):
    follows_col = get_follows_collection()
    channels_col = get_channels_collection()

    following_ids = []
    async for f in follows_col.find({"user_id": current_user.id}):
        following_ids.append(f["channel_id"])

    if not following_ids:
        return []

    result = []
    for ch_id in following_ids:
        doc = await channels_col.find_one({"id": ch_id})
        if doc:
            count = await get_song_count(ch_id)
            access = await get_access_status(
                ch_id, current_user.id,
                doc.get("owner_id", ""), doc.get("is_public", True)
            )
            result.append(
                channel_doc_to_response(doc, count, True, access)
            )
    return result

@router.get("", response_model=List[ChannelResponse])
async def all_channels(
    current_user: Optional[User] = Depends(get_optional_user)
):
    channels_col = get_channels_collection()
    user_id = current_user.id if current_user else None

    query = {"is_public": True}
    if user_id:
        query["owner_id"] = {"$ne": user_id}

    result = []
    async for doc in channels_col.find(query):
        count = await get_song_count(doc.get("id", ""))
        following = await is_following(doc.get("id", ""), user_id) \
            if user_id else False
        access = await get_access_status(
            doc.get("id", ""), user_id,
            doc.get("owner_id", ""), doc.get("is_public", True)
        ) if user_id else "none"
        result.append(channel_doc_to_response(doc, count, following, access))
    return result

@router.post("", response_model=ChannelResponse)
async def create_channel(
    body: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    channels_col = get_channels_collection()
    users_col = get_users_collection()

    # Check already has channel
    existing = await channels_col.find_one({"owner_id": current_user.id})
    if existing:
        raise HTTPException(status_code=400, detail="You already have a channel")

    name = body.get("name", "").strip()
    description = body.get("description", "")
    is_public_raw = body.get("isPublic", "true")
    if isinstance(is_public_raw, bool):
        is_public = is_public_raw
    else:
        is_public = str(is_public_raw).lower() not in ["false", "0", "no"]

    if not name:
        raise HTTPException(status_code=400, detail="Channel name required")

    channel_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    channel_doc = {
        "_id": channel_id,
        "id": channel_id,
        "name": name,
        "description": description,
        "is_public": is_public,
        "owner_id": current_user.id,
        "owner_name": current_user.username,
        "cover_url": None,
        "follower_count": 0,
        "created_at": now
    }

    await channels_col.insert_one(channel_doc)

    # Update user's channel_id
    await users_col.update_one(
        {"id": current_user.id},
        {"$set": {"channel_id": channel_id}}
    )

    logger.info(f"Channel created: {name} by {current_user.username}")
    return channel_doc_to_response(channel_doc, 0, False, "owner")

@router.get("/{channel_id}", response_model=ChannelResponse)
async def channel_by_id(
    channel_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    channels_col = get_channels_collection()
    doc = await channels_col.find_one({"id": channel_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Channel not found")

    user_id = current_user.id if current_user else None
    count = await get_song_count(channel_id)
    following = await is_following(channel_id, user_id) if user_id else False
    access = await get_access_status(
        channel_id, user_id,
        doc.get("owner_id", ""), doc.get("is_public", True)
    )
    return channel_doc_to_response(doc, count, following, access)

@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str,
    body: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    channels_col = get_channels_collection()
    doc = await channels_col.find_one({"id": channel_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Channel not found")
    if doc.get("owner_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not your channel")

    updates = {}
    name = body.get("name", "").strip()
    description = body.get("description")
    is_public_raw = body.get("isPublic")

    if name:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if is_public_raw is not None:
        if isinstance(is_public_raw, bool):
            updates["is_public"] = is_public_raw
        else:
            updates["is_public"] = str(is_public_raw).lower() not in [
                "false", "0", "no"
            ]

    if updates:
        await channels_col.update_one(
            {"id": channel_id}, {"$set": updates}
        )

    updated = await channels_col.find_one({"id": channel_id})
    count = await get_song_count(channel_id)
    logger.info(f"Channel updated: {channel_id}")
    return channel_doc_to_response(updated, count, False, "owner")

@router.post("/{channel_id}/follow")
async def follow_channel(
    channel_id: str,
    current_user: User = Depends(get_current_user)
):
    channels_col = get_channels_collection()
    doc = await channels_col.find_one({"id": channel_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Channel not found")
    if doc.get("owner_id") == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow own channel")

    follows_col = get_follows_collection()
    existing = await follows_col.find_one({
        "channel_id": channel_id, "user_id": current_user.id
    })

    if existing:
        await follows_col.delete_one({"_id": existing["_id"]})
        new_count = max(0, doc.get("follower_count", 0) - 1)
        await channels_col.update_one(
            {"id": channel_id},
            {"$set": {"follower_count": new_count}}
        )
        return {"action": "unfollowed", "follower_count": new_count}
    else:
        await follows_col.insert_one({
            "channel_id": channel_id,
            "user_id": current_user.id,
            "followed_at": datetime.datetime.utcnow()
        })
        new_count = doc.get("follower_count", 0) + 1
        await channels_col.update_one(
            {"id": channel_id},
            {"$set": {"follower_count": new_count}}
        )
        return {"action": "followed", "follower_count": new_count}

@router.post("/{channel_id}/request-access")
async def request_access(
    channel_id: str,
    current_user: User = Depends(get_current_user)
):
    channels_col = get_channels_collection()
    doc = await channels_col.find_one({"id": channel_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Channel not found")
    if doc.get("is_public", True):
        raise HTTPException(status_code=400, detail="Channel is public")
    if doc.get("owner_id") == current_user.id:
        raise HTTPException(status_code=400, detail="You own this channel")

    access_col = get_granted_access_collection()
    if await access_col.find_one(
        {"channel_id": channel_id, "user_id": current_user.id}
    ):
        raise HTTPException(status_code=400, detail="Already have access")

    req_col = get_access_requests_collection()
    if await req_col.find_one({
        "channel_id": channel_id,
        "user_id": current_user.id,
        "status": "pending"
    }):
        raise HTTPException(status_code=400, detail="Request already pending")

    request_id = str(uuid.uuid4())
    await req_col.insert_one({
        "_id": request_id,
        "id": request_id,
        "channel_id": channel_id,
        "channel_name": doc.get("name", ""),
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "status": "pending",
        "created_at": datetime.datetime.utcnow()
    })
    return {"success": True, "message": "Request sent to channel owner"}

@router.get(
    "/{channel_id}/access-requests",
    response_model=List[AccessRequestResponse]
)
async def get_access_requests(
    channel_id: str,
    current_user: User = Depends(get_current_user)
):
    channels_col = get_channels_collection()
    doc = await channels_col.find_one({"id": channel_id})
    if not doc or doc.get("owner_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not your channel")

    req_col = get_access_requests_collection()
    requests = []
    async for req in req_col.find(
        {"channel_id": channel_id, "status": "pending"}
    ):
        created_at = req.get("created_at")
        created_at_ms = int(created_at.timestamp() * 1000) \
            if hasattr(created_at, "timestamp") else 0
        requests.append(AccessRequestResponse(
            id=req.get("id", str(req.get("_id", ""))),
            channel_id=channel_id,
            user_id=req.get("user_id", ""),
            username=req.get("username", ""),
            email=req.get("email", ""),
            status=req.get("status", "pending"),
            created_at=created_at_ms
        ))
    return requests

@router.post("/{channel_id}/grant-access/{user_id}")
async def grant_access(
    channel_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    channels_col = get_channels_collection()
    doc = await channels_col.find_one({"id": channel_id})
    if not doc or doc.get("owner_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not your channel")

    req_col = get_access_requests_collection()
    await req_col.update_one(
        {"channel_id": channel_id, "user_id": user_id},
        {"$set": {"status": "granted"}}
    )

    access_col = get_granted_access_collection()
    await access_col.insert_one({
        "_id": str(uuid.uuid4()),
        "channel_id": channel_id,
        "user_id": user_id,
        "granted_by": current_user.id,
        "status": "granted",
        "granted_at": datetime.datetime.utcnow()
    })
    return {"success": True, "message": "Access granted"}

@router.get("/{channel_id}/reject-access/{user_id}")
async def reject_access(
    channel_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    channels_col = get_channels_collection()
    doc = await channels_col.find_one({"id": channel_id})
    if not doc or doc.get("owner_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not your channel")

    req_col = get_access_requests_collection()
    await req_col.update_one(
        {"channel_id": channel_id, "user_id": user_id},
        {"$set": {"status": "rejected"}}
    )
    return {"success": True, "message": "Request rejected"}

@router.get("/{channel_id}/check-access")
async def check_access(
    channel_id: str,
    current_user: User = Depends(get_current_user)
):
    channels_col = get_channels_collection()
    doc = await channels_col.find_one({"id": channel_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Channel not found")

    access = await get_access_status(
        channel_id, current_user.id,
        doc.get("owner_id", ""), doc.get("is_public", True)
    )
    return {"channel_id": channel_id, "access_status": access}

@router.delete("/{channel_id}/songs/{song_id}")
async def delete_song(
    channel_id: str,
    song_id: str,
    current_user: User = Depends(get_current_user)
):
    """Owner deletes song - removes from MongoDB + Cloudinary"""
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

    songs_col = get_songs_collection()
    song = await songs_col.find_one({
        "id": song_id,
        "channel_id": channel_id
    })

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # Step 1: Delete files from storage
    deleted_files = []
    failed_files = []

    try:
        from app.storage.factory import get_storage
        storage = get_storage()

        audio_file_id = song.get("audio_file_id")
        if audio_file_id:
            success = await storage.delete_file(audio_file_id)
            if success:
                deleted_files.append("audio")
                logger.info(f"✅ Audio deleted: {audio_file_id}")
            else:
                failed_files.append("audio")
                logger.error(f"❌ Audio delete failed: {audio_file_id}")

        cover_file_id = song.get("cover_file_id")
        if cover_file_id:
            success = await storage.delete_file(cover_file_id)
            if success:
                deleted_files.append("cover")
                logger.info(f"✅ Cover deleted: {cover_file_id}")
            else:
                failed_files.append("cover")

        lyrics_file_id = song.get("lyrics_file_id")
        if lyrics_file_id:
            success = await storage.delete_file(lyrics_file_id)
            if success:
                deleted_files.append("lyrics")
                logger.info(f"✅ Lyrics deleted: {lyrics_file_id}")
            else:
                failed_files.append("lyrics")

    except Exception as e:
        logger.error(f"Storage delete error: {e}")

    # Step 2: HARD DELETE from MongoDB (not soft delete)
    await songs_col.delete_one({"id": song_id})

    # Step 3: Also delete related likes
    from app.mongodb import get_likes_collection
    likes_col = get_likes_collection()
    await likes_col.delete_many({"song_id": song_id})

    logger.info(
        f"Song {song_id} deleted. "
        f"Files deleted: {deleted_files}. "
        f"Failed: {failed_files}"
    )

    return {
        "success": True,
        "message": "Song deleted",
        "deleted_files": deleted_files,
        "failed_files": failed_files
    }