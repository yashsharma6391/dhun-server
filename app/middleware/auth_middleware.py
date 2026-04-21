from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.utils.jwt_handler import verify_token
from app.models.user import User
from app.mongodb import get_users_collection
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    raw_token = credentials.credentials

    # Auto fix Bearer prefix
    if raw_token.startswith("Bearer ") or raw_token.startswith("bearer "):
        raw_token = raw_token.replace("Bearer ", "").replace("bearer ", "").strip()

    user_id = verify_token(raw_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    users_col = get_users_collection()
    user_doc = await users_col.find_one({"id": user_id})

    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    logger.info(f"Auth SUCCESS - user:{user_doc.get('email')}")
    return User.from_dict(user_doc)

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_optional)
) -> Optional[User]:
    if not credentials:
        return None
    try:
        raw_token = credentials.credentials
        if raw_token.startswith("Bearer ") or raw_token.startswith("bearer "):
            raw_token = raw_token.replace("Bearer ", "").replace("bearer ", "").strip()

        user_id = verify_token(raw_token)
        if not user_id:
            return None

        users_col = get_users_collection()
        user_doc = await users_col.find_one({"id": user_id})
        return User.from_dict(user_doc) if user_doc else None
    except Exception:
        return None