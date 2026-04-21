from datetime import datetime
import uuid

class Channel:
    """
    Channel model for MongoDB
    No SQLAlchemy - pure Python
    """
    def __init__(
        self,
        name: str,
        owner_id: str,
        id: str = None,
        description: str = "",
        cover_url: str = None,
        is_public: bool = True,
        follower_count: int = 0,
        created_at: datetime = None,
        owner_name: str = ""
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.owner_id = owner_id
        self.description = description
        self.cover_url = cover_url
        self.is_public = is_public
        self.follower_count = follower_count
        self.created_at = created_at or datetime.utcnow()
        self.owner_name = owner_name

    def to_dict(self) -> dict:
        return {
            "_id": self.id,
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "description": self.description,
            "cover_url": self.cover_url,
            "is_public": self.is_public,
            "follower_count": self.follower_count,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Channel":
        if not data:
            return None
        return cls(
            id=data.get("id", str(data.get("_id", ""))),
            name=data.get("name", ""),
            owner_id=data.get("owner_id", ""),
            description=data.get("description", ""),
            cover_url=data.get("cover_url"),
            is_public=data.get("is_public", True),
            follower_count=data.get("follower_count", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            owner_name=data.get("owner_name", "")
        )

    def __repr__(self):
        return f"<Channel {self.name}>"