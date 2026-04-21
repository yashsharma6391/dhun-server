from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

# Association table for playlist songs
playlist_songs = Table(
    "playlist_songs",
    Base.metadata,
    Column("playlist_id", String, ForeignKey("playlists.id")),
    Column("song_id", String, ForeignKey("songs.id")),
)

class Playlist(Base):
    __tablename__ = "playlists"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True, default="")
    cover_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign key
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    songs = relationship("Song", secondary=playlist_songs)
    
    def __repr__(self):
        return f"<Playlist {self.name}>"