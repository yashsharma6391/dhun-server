from pydantic import BaseModel
from typing import Optional

class SongResponse(BaseModel):
    id: str
    title: str
    artist: str
    album: Optional[str] = ""
    duration: Optional[int] = 0
    cover_url: Optional[str] = None
    audio_url: str
    lyrics_url: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    uploaded_at: Optional[int] = None
    play_count: Optional[int] = 0
    file_size: Optional[int] = 0
    # NEW: Like fields
    like_count: Optional[int] = 0
    dislike_count: Optional[int] = 0
    user_liked: Optional[bool] = False
    user_disliked: Optional[bool] = False

    class Config:
        from_attributes = True