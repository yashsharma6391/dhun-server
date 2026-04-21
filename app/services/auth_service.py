from fastapi import HTTPException, status
import logging
import traceback
import uuid
from datetime import datetime

from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from app.utils.password_handler import hash_password, verify_password
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.mongodb import get_users_collection

logger = logging.getLogger(__name__)

async def register_user(request: RegisterRequest) -> AuthResponse:
    logger.info(f"register_user - email:{request.email} name:{request.name}")
    users_col = get_users_collection()

    try:
        # Check email exists
        existing_email = await users_col.find_one({"email": request.email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check username exists
        existing_username = await users_col.find_one({"username": request.name})
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Hash password
        hashed = hash_password(request.password)

        # Create user
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        user_doc = {
            "_id": user_id,
            "id": user_id,
            "username": request.name,
            "email": request.email,
            "hashed_password": hashed,
            "profile_pic_url": None,
            "is_active": True,
            "is_verified": False,
            "created_at": now,
            "updated_at": now,
            "channel_id": None
        }

        await users_col.insert_one(user_doc)
        logger.info(f"User created - id:{user_id}")

        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        return AuthResponse(
            token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                id=user_id,
                username=request.name,
                email=request.email,
                profile_pic_url=None,
                channel_id=None,
                created_at=int(now.timestamp() * 1000)
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"register_user FAILED: {e}")
        logger.error(traceback.format_exc())
        raise

async def login_user(request: LoginRequest) -> AuthResponse:
    logger.info(f"login_user - email:{request.email}")
    users_col = get_users_collection()

    try:
        user_doc = await users_col.find_one({"email": request.email})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not verify_password(request.password, user_doc["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        user_id = user_doc.get("id", str(user_doc.get("_id", "")))
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        created_at = user_doc.get("created_at", datetime.utcnow())
        created_at_ms = int(created_at.timestamp() * 1000) \
            if hasattr(created_at, "timestamp") else 0

        logger.info(f"login SUCCESS - user:{user_id}")

        return AuthResponse(
            token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                id=user_id,
                username=user_doc.get("username", ""),
                email=user_doc.get("email", ""),
                profile_pic_url=user_doc.get("profile_pic_url"),
                channel_id=user_doc.get("channel_id"),
                created_at=created_at_ms
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"login FAILED: {e}")
        raise