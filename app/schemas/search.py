from pydantic import BaseModel
from typing import List
from app.schemas.song import SongResponse
from app.schemas.channel import ChannelResponse

class SearchResultResponse(BaseModel):
    songs: List[SongResponse] = []
    channels: List[ChannelResponse] = []