from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    profile_pic_url: Optional[str] = None
    channel_id: Optional[str] = None
    created_at: Optional[int] = None

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    token: str
    refresh_token: str
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[str] = None