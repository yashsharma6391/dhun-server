import bcrypt
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    try:
        # Encode password to bytes
        password_bytes = password.encode('utf-8')
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        logger.debug("Password hashed successfully")
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Hash password error: {e}")
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        result = bcrypt.checkpw(password_bytes, hashed_bytes)
        logger.debug(f"Password verify result: {result}")
        return result
    except Exception as e:
        logger.error(f"Verify password error: {e}")
        return False