from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.channel import Channel
from app.models.user import User
from app.schemas.channel import ChannelResponse, ChannelCreateRequest
from typing import List

def get_popular_channels(db: Session) -> List[ChannelResponse]:
    channels = db.query(Channel)\
        .filter(Channel.is_public == True)\
        .order_by(Channel.follower_count.desc())\
        .limit(20)\
        .all()
    return [channel_to_response(c) for c in channels]

def get_all_channels(db: Session) -> List[ChannelResponse]:
    channels = db.query(Channel)\
        .filter(Channel.is_public == True)\
        .all()
    return [channel_to_response(c) for c in channels]

def get_channel_by_id(channel_id: str, db: Session) -> ChannelResponse:
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    return channel_to_response(channel)

def get_my_channel(user: User, db: Session):
    channel = db.query(Channel)\
        .filter(Channel.owner_id == user.id)\
        .first()
    if not channel:
        return None
    return channel_to_response(channel)

def create_channel(
    request: dict,
    user: User,
    db: Session
) -> ChannelResponse:
    # Check user already has a channel
    existing = db.query(Channel)\
        .filter(Channel.owner_id == user.id)\
        .first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a channel"
        )
    
    name = request.get("name", "")
    description = request.get("description", "")
    is_public = request.get("isPublic", "true").lower() == "true"
    
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Channel name is required"
        )
    
    channel = Channel(
        name=name,
        description=description,
        is_public=is_public,
        owner_id=user.id
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    
    return channel_to_response(channel)

def channel_to_response(channel: Channel) -> ChannelResponse:
    owner_name = ""
    try:
        owner_name = channel.owner.username if channel.owner else ""
    except Exception:
        pass
    
    return ChannelResponse(
        id=channel.id,
        name=channel.name,
        description=channel.description or "",
        owner_name=owner_name,
        owner_id=channel.owner_id,
        cover_url=channel.cover_url,
        song_count=len(channel.songs) if channel.songs else 0,
        follower_count=channel.follower_count or 0,
        created_at=int(channel.created_at.timestamp() * 1000) if channel.created_at else 0
    )