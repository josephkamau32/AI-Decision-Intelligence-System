"""
User models and schemas for authentication
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for user update"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserInDB(UserBase):
    """User schema in database"""
    id: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """User response schema (no password)"""
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """JWT token payload"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


class APIKeyCreate(BaseModel):
    """API key creation schema"""
    name: str = Field(..., description="Name/description for the API key")
    expires_in_days: Optional[int] = Field(None, description="Days until expiration (None = no expiration)")


class APIKeyResponse(BaseModel):
    """API key response"""
    key: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
