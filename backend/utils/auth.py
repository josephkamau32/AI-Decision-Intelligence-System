"""
Complete Authentication & Authorization System
Implements JWT tokens, password hashing, RBAC, and API key authentication
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib
from .config import settings

# Configure logger
logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

# Persistent storage (uses JSON files instead of in-memory dictionaries)
from .storage import users_storage, api_keys_storage

# For backward compatibility, create dictionary-like references
users_db = users_storage
api_keys_db = api_keys_storage


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


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
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
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
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
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
        HTTPException: If username or email already exists or validation fails
    """
    # Validate password strength
    from .validators import validate_password_strength, validate_email
    
    password_validation = validate_password_strength(password)
    if not password_validation.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {'; '.join(password_validation.errors)}"
        )
    
    # Validate email format
    email_validation = validate_email(email)
    if not email_validation.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email validation failed: {'; '.join(email_validation.errors)}"
        )
    
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
        "updated_at": datetime.utcnow(),
        "failed_login_attempts": 0,
        "last_login": None
    }
    
    users_db[user_id] = user
    
    # Log security event
    logger.info(f"New user registered: {username} (ID: {user_id})")
    
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
    user_id = None
    for uid, u in users_db.items():
        if u["username"] == username:
            user = u
            user_id = uid
            break
    
    if not user:
        logger.warning(f"Authentication failed: User not found - {username}")
        return None
    
    # Check if account is locked due to failed attempts
    if user.get("failed_login_attempts", 0) >= 5:
        logger.warning(f"Authentication blocked: Too many failed attempts - {username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed login attempts. Please try again later."
        )
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        # Increment failed attempts
        user["failed_login_attempts"] = user.get("failed_login_attempts", 0) + 1
        users_db[user_id] = user
        logger.warning(f"Authentication failed: Incorrect password - {username} (attempts: {user['failed_login_attempts']})")
        return None
    
    # Check if active
    if not user.get("is_active", True):
        logger.warning(f"Authentication failed: Inactive account - {username}")
        return None
    
    # Reset failed attempts on successful login
    user["failed_login_attempts"] = 0
    user["last_login"] = datetime.utcnow()
    users_db[user_id] = user
    
    logger.info(f"Authentication successful: {username}")
    
    return user
