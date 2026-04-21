from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from typing import Optional
import logging
import traceback
from datetime import datetime

from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from app.services.auth_service import register_user, login_user
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.storage.factory import get_storage
from app.utils.jwt_handler import create_access_token, create_refresh_token, verify_token
from app.mongodb import get_users_collection, get_songs_collection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    logger.info(f"Register - name:{request.name} email:{request.email}")
    try:
        return await register_user(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    logger.info(f"Login - email:{request.email}")
    try:
        return await login_user(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    logger.info(f"Logout - user:{current_user.email}")
    return {"success": True}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    try:
        created_at = current_user.created_at
        created_at_ms = int(created_at.timestamp() * 1000) \
            if hasattr(created_at, "timestamp") else 0

        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            profile_pic_url=current_user.profile_pic_url,
            channel_id=current_user.channel_id,
            created_at=created_at_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token_endpoint(body: dict = Body(...)):
    refresh_tok = body.get("refresh_token")
    if not refresh_tok:
        raise HTTPException(status_code=400, detail="Refresh token required")

    user_id = verify_token(refresh_tok)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token. Please login again."
        )

    users_col = get_users_collection()
    user_doc = await users_col.find_one({"id": user_id})
    if not user_doc or not user_doc.get("is_active", True):
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)

    created_at = user_doc.get("created_at", datetime.utcnow())
    created_at_ms = int(created_at.timestamp() * 1000) \
        if hasattr(created_at, "timestamp") else 0

    logger.info(f"Token refreshed: {user_doc.get('email')}")
    return AuthResponse(
        token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse(
            id=user_id,
            username=user_doc.get("username", ""),
            email=user_doc.get("email", ""),
            profile_pic_url=user_doc.get("profile_pic_url"),
            channel_id=user_doc.get("channel_id"),
            created_at=created_at_ms
        )
    )

@router.put("/update-profile", response_model=UserResponse)
async def update_profile(
    body: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    try:
        users_col = get_users_collection()
        updates = {"updated_at": datetime.utcnow()}

        new_username = body.get("username", "").strip()
        new_email = body.get("email", "").strip()

        if new_username and new_username != current_user.username:
            existing = await users_col.find_one({"username": new_username})
            if existing:
                raise HTTPException(status_code=400, detail="Username taken")
            updates["username"] = new_username

        if new_email and new_email != current_user.email:
            existing = await users_col.find_one({"email": new_email})
            if existing:
                raise HTTPException(status_code=400, detail="Email in use")
            updates["email"] = new_email

        await users_col.update_one(
            {"id": current_user.id},
            {"$set": updates}
        )

        updated = await users_col.find_one({"id": current_user.id})
        created_at = updated.get("created_at", datetime.utcnow())
        created_at_ms = int(created_at.timestamp() * 1000) \
            if hasattr(created_at, "timestamp") else 0

        logger.info(f"Profile updated: {current_user.id}")
        return UserResponse(
            id=current_user.id,
            username=updated.get("username", ""),
            email=updated.get("email", ""),
            profile_pic_url=updated.get("profile_pic_url"),
            channel_id=updated.get("channel_id"),
            created_at=created_at_ms
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-profile-pic", response_model=UserResponse)
async def upload_profile_pic(
    profile_pic: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        storage = get_storage()
        content = await profile_pic.read()
        result = await storage.upload_cover(
            file_content=content,
            filename=profile_pic.filename or "profile.jpg",
            content_type=profile_pic.content_type or "image/jpeg"
        )

        users_col = get_users_collection()
        await users_col.update_one(
            {"id": current_user.id},
            {"$set": {
                "profile_pic_url": result.public_url,
                "updated_at": datetime.utcnow()
            }}
        )

        created_at = current_user.created_at
        created_at_ms = int(created_at.timestamp() * 1000) \
            if hasattr(created_at, "timestamp") else 0

        logger.info(f"Profile pic uploaded: {current_user.email}")
        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            profile_pic_url=result.public_url,
            channel_id=current_user.channel_id,
            created_at=created_at_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-channel-stats")
async def my_channel_stats(
    current_user: User = Depends(get_current_user)
):
    channel_id = current_user.channel_id
    if not channel_id:
        return {
            "total_songs": 0,
            "total_likes": 0,
            "total_dislikes": 0,
            "songs": []
        }

    songs_col = get_songs_collection()
    songs_stats = []
    total_likes = 0
    total_dislikes = 0

    async for song in songs_col.find(
        {"channel_id": channel_id, "is_active": True}
    ):
        lc = song.get("like_count", 0)
        dc = song.get("dislike_count", 0)
        total_likes += lc
        total_dislikes += dc
        songs_stats.append({
            "id": song.get("id"),
            "title": song.get("title"),
            "like_count": lc,
            "dislike_count": dc,
            "play_count": song.get("play_count", 0)
        })

    return {
        "channel_id": channel_id,
        "total_songs": len(songs_stats),
        "total_likes": total_likes,
        "total_dislikes": total_dislikes,
        "songs": songs_stats
    }