# Playlist model - pure Python for MongoDB
from datetime import datetime
import uuid

class Playlist:
    def __init__(
        self,
        name: str,
        owner_id: str,
        id: str = None,
        description: str = "",
        cover_url: str = None,
        created_at: datetime = None
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.owner_id = owner_id
        self.description = description
        self.cover_url = cover_url
        self.created_at = created_at or datetime.utcnow()