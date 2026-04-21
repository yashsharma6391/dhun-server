from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug(f"Token created for user:{user_id}")
    logger.debug(f"SECRET_KEY used: {settings.SECRET_KEY[:20]}...")
    logger.debug(f"Token preview: {token[:50]}...")
    return token

def create_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str) -> Optional[str]:
    logger.debug(f"Verifying token: {token[:50]}...")
    logger.debug(f"SECRET_KEY used: {settings.SECRET_KEY[:20]}...")
    logger.debug(f"ALGORITHM: {settings.ALGORITHM}")
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        logger.debug(f"Token decoded successfully: {payload}")
        
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        exp = payload.get("exp")
        
        logger.debug(f"user_id from token: {user_id}")
        logger.debug(f"token_type: {token_type}")
        logger.debug(f"expires: {exp}")
        
        if user_id is None:
            logger.error("Token has no sub field")
            return None
            
        return user_id
        
    except JWTError as e:
        logger.error(f"JWT Error: {type(e).__name__}: {str(e)}")
        logger.error(f"Token that failed: {token}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {e}")
        return None