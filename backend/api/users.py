"""
User Management API Endpoints
Handles registration, login, and user profile management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import timedelta

from ..schemas.users import (
    UserCreate, UserResponse, UserUpdate, LoginRequest,
    Token, APIKeyCreate, APIKeyResponse
)
from ..utils.auth import (
    register_user, authenticate_user, create_access_token,
    get_current_user, create_api_key, require_admin,
    users_db
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **role**: User role (default: user)
    """
    user = register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role.value
    )
    
    return user


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return JWT token
    
    - **username**: Username
    - **password**: Password
    
    Returns JWT access token for subsequent API calls
    """
    user = authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800  # 30 minutes in seconds
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user profile
    
    Requires authentication via JWT token
    """
    # Remove hashed_password from response
    return {k: v for k, v in current_user.items() if k != "hashed_password"}


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current user profile
    
    Can update:
    - email
    - full_name
    - password
    """
    user_id = current_user["id"]
    user = users_db[user_id]
    
    # Update fields
    if user_update.email:
        # Check if email already exists
        for uid, u in users_db.items():
            if u["email"] == user_update.email and uid != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        user["email"] = user_update.email
    
    if user_update.full_name is not None:
        user["full_name"] = user_update.full_name
    
    if user_update.password:
        from ..utils.auth import get_password_hash
        user["hashed_password"] = get_password_hash(user_update.password)
    
    # Save updated user
    users_db[user_id] = user
    
    return {k: v for k, v in user.items() if k != "hashed_password"}


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_new_api_key(
    api_key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a new API key for the current user
    
    - **name**: Description for the API key
    - **expires_in_days**: Optional expiration (None = never expires)
    
    ⚠️ Save the API key securely - it won't be shown again!
    """
    api_key = create_api_key(
        user_id=current_user["id"],
        name=api_key_data.name,
        expires_in_days=api_key_data.expires_in_days
    )
    
    from datetime import datetime, timedelta
    expires_at = None
    if api_key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)
    
    return {
        "key": api_key,
        "name": api_key_data.name,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    }


@router.get("/", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(require_admin)):
    """
    List all users (admin only)
    
    Requires admin role
    """
    users = [
        {k: v for k, v in user.items() if k != "hashed_password"}
        for user in users_db.values()
    ]
    return users


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    """
    Delete a user (admin only)
    
    Requires admin role
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting yourself
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    del users_db[user_id]
    
    return {"message": "User deleted successfully"}
