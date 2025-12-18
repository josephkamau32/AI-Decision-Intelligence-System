"""
Complete Authentication & Authorization System
Implements JWT tokens, password hashing, RBAC, and API key authentication
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib
from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

# In-memory user store (replace with database in production)
users_db: Dict[str, Dict[str, Any]] = {}
api_keys_db: Dict[str, Dict[str, Any]] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data (must include 'sub' for username)
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=getattr(settings, 'jwt_expiration_minutes', 30))
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    secret_key = getattr(settings, 'jwt_secret_key', settings.secret_key)
    algorithm = getattr(settings, 'jwt_algorithm', 'HS256')
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return payload
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        secret_key = getattr(settings, 'jwt_secret_key', settings.secret_key)
        algorithm = getattr(settings, 'jwt_algorithm', 'HS256')
        
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        return None


def create_api_key(user_id: str, name: str, expires_in_days: Optional[int] = None) -> str:
    """
    Generate a new API key
    
    Args:
        user_id: User ID who owns the key
        name: Description for the key
        expires_in_days: Days until expiration (None = never expires)
        
    Returns:
        Generated API key
    """
    # Generate random key
    key = f"sk_{secrets.token_urlsafe(32)}"
    
    # Hash the key for storage
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    # Store key metadata
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    api_keys_db[key_hash] = {
        "user_id": user_id,
        "name": name,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "is_active": True
    }
    
    return key


def verify_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Verify API key and return associated user data
    
    Args:
        api_key: API key string
        
    Returns:
        User data if key is valid, None otherwise
    """
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    key_data = api_keys_db.get(key_hash)
    if not key_data:
        return None
    
    # Check if expired
    if key_data.get("expires_at"):
        if datetime.utcnow() > key_data["expires_at"]:
            return None
    
    # Check if active
    if not key_data.get("is_active", True):
        return None
    
    # Get user
    user_id = key_data["user_id"]
    return users_db.get(user_id)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        Current user data
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    user = users_db.get(user_id)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_user_or_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get current user from either JWT token or API key
    
    Supports both:
    - Authorization: Bearer <jwt_token>
    - X-API-Key: <api_key>
    
    Args:
        credentials: HTTP Authorization credentials (JWT)
        x_api_key: API key from header
        
    Returns:
        Current user data
        
    Raises:
        HTTPException: If authentication fails
    """
    # Try API key first
    if x_api_key:
        user = verify_api_key(x_api_key)
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Try JWT token
    if credentials:
        return await get_current_user(credentials)
    
    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(required_role: str):
    """
    Dependency to require specific user role
    
    Args:
        required_role: Required role (admin, user, viewer)
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "viewer")
        
        # Role hierarchy: admin > user > viewer
        role_hierarchy = {"admin": 3, "user": 2, "viewer": 1}
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}"
            )
        
        return current_user
    
    return role_checker


# Convenience dependencies
require_admin = require_role("admin")
require_user = require_role("user")
require_viewer = require_role("viewer")


def register_user(username: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
    """
    Register a new user
    
    Args:
        username: Username
        email: Email address
        password: Plain password
        role: User role (admin, user, viewer)
        
    Returns:
        Created user data (without password)
        
    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username exists
    for user_id, user in users_db.items():
        if user["username"] == username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        if user["email"] == email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Create user
    user_id = f"user_{secrets.token_urlsafe(16)}"
    hashed_password = get_password_hash(password)
    
    user = {
        "id": user_id,
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "role": role,
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    users_db[user_id] = user
    
    # Return user without password
    return {k: v for k, v in user.items() if k != "hashed_password"}


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with username and password
    
    Args:
        username: Username
        password: Plain password
        
    Returns:
        User data if authentication successful, None otherwise
    """
    # Find user
    user = None
    for user_id, u in users_db.items():
        if u["username"] == username:
            user = u
            break
    
    if not user:
        return None
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        return None
    
    # Check if active
    if not user.get("is_active", True):
        return None
    
    return user
