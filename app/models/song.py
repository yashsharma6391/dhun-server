# from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, ForeignKey
# from sqlalchemy.orm import relationship
# from datetime import datetime
# import uuid
# from app.database import Base

# class Song(Base):
#     __tablename__ = "songs"

#     id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     title = Column(String(200), nullable=False, index=True)
#     artist = Column(String(200), nullable=False, index=True)
#     album = Column(String(200), nullable=True)
#     duration = Column(BigInteger, default=0)
#     cover_url = Column(String, nullable=True)
#     audio_url = Column(String, nullable=False)
#     # FIXED: Added lyrics_url
#     lyrics_url = Column(String, nullable=True)
#     file_size = Column(BigInteger, default=0)
#     play_count = Column(Integer, default=0)
#     is_active = Column(Boolean, default=True)
#     uploaded_at = Column(DateTime, default=datetime.utcnow)

#     channel_id = Column(String, ForeignKey("channels.id"), nullable=True)
#     uploaded_by = Column(String, ForeignKey("users.id"), nullable=True)

#     channel = relationship("Channel", back_populates="songs")

#     def __repr__(self):
#         return f"<Song {self.title}>"