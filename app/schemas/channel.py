from pydantic import BaseModel
from typing import Optional, List

class ChannelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    owner_name: Optional[str] = ""
    owner_id: Optional[str] = ""
    cover_url: Optional[str] = None
    song_count: Optional[int] = 0
    follower_count: Optional[int] = 0
    created_at: Optional[int] = None
    is_public: Optional[bool] = True
    # NEW fields
    is_following: Optional[bool] = False
    access_status: Optional[str] = "none"
    # none | pending | granted | owner

    class Config:
        from_attributes = True

class AccessRequestResponse(BaseModel):
    id: str
    channel_id: str
    user_id: str
    username: str
    email: str
    status: str  # pending | granted | rejected
    created_at: int