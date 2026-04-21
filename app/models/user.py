# Pure Python class - no SQLAlchemy
# Data stored in MongoDB users collection
from datetime import datetime
import uuid

class User:
    """
    User model for MongoDB
    No SQLAlchemy - pure Python
    """
    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        id: str = None,
        profile_pic_url: str = None,
        is_active: bool = True,
        is_verified: bool = False,
        created_at: datetime = None,
        updated_at: datetime = None,
        channel_id: str = None
    ):
        self.id = id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.profile_pic_url = profile_pic_url
        self.is_active = is_active
        self.is_verified = is_verified
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.channel_id = channel_id

    def to_dict(self) -> dict:
        return {
            "_id": self.id,
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "profile_pic_url": self.profile_pic_url,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "channel_id": self.channel_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        if not data:
            return None
        return cls(
            id=data.get("id", str(data.get("_id", ""))),
            username=data.get("username", ""),
            email=data.get("email", ""),
            hashed_password=data.get("hashed_password", ""),
            profile_pic_url=data.get("profile_pic_url"),
            is_active=data.get("is_active", True),
            is_verified=data.get("is_verified", False),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            channel_id=data.get("channel_id")
        )

    def __repr__(self):
        return f"<User {self.username}>"