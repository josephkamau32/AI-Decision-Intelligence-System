"""
Centralized Error Handling System
Provides custom exceptions, error formatters, and error logging utilities
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


# Custom Exception Classes
class DeciseraException(Exception):
    """Base exception for Decisera application"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(DeciseraException):
    """Validation error exception"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class AuthenticationError(DeciseraException):
    """Authentication error exception"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)


class AuthorizationError(DeciseraException):
    """Authorization error exception"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, details)


class ResourceNotFoundError(DeciseraException):
    """Resource not found exception"""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} not found: {resource_id}"
        super().__init__(message, status.HTTP_404_NOT_FOUND, {
            "resource_type": resource_type,
            "resource_id": resource_id
        })


class RateLimitError(DeciseraException):
    """Rate limit exceeded exception"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS, {
            "retry_after": retry_after
        })


class ExternalServiceError(DeciseraException):
    """External service error exception"""
    def __init__(self, service: str, message: str):
        super().__init__(
            f"External service error ({service}): {message}",
            status.HTTP_502_BAD_GATEWAY,
            {"service": service}
        )


class ModelError(DeciseraException):
    """ML Model error exception"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class DataProcessingError(DeciseraException):
    """Data processing error exception"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


# Error Response Formatters
def format_error_response(
    error: Exception,
    request: Optional[Request] = None,
    include_trace: bool = False
) -> Dict[str, Any]:
    """
    Format error into standardized response structure
    
    Args:
        error: The exception that occurred
        request: Optional request object for context
        include_trace: Whether to include stack trace (debug mode only)
        
    Returns:
        Formatted error response dictionary
    """
    if isinstance(error, DeciseraException):
        response = {
            "error": {
                "code": error.status_code,
                "message": error.message,
                "details": error.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    elif isinstance(error, HTTPException):
        response = {
            "error": {
                "code": error.status_code,
                "message": error.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    else:
        # Generic exception
        response = {
            "error": {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An internal server error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    # Add request path if available
    if request:
        response["error"]["path"] = str(request.url.path)
    
    # Add stack trace in debug mode
    if include_trace:
        response["error"]["trace"] = traceback.format_exc()
    
    return response


def log_error(
    error: Exception,
    request: Optional[Request] = None,
    context: Optional[Dict[str, Any]] = None
):
    """
    Log error with context information
    
    Args:
        error: The exception that occurred
        request: Optional request object
        context: Additional context information
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Build log message
    log_parts = [f"{error_type}: {error_msg}"]
    
    if request:
        log_parts.append(f"Path: {request.url.path}")
        log_parts.append(f"Method: {request.method}")
    
    if context:
        log_parts.append(f"Context: {context}")
    
    log_message = " | ".join(log_parts)
    
    # Log with appropriate level
    if isinstance(error, (ValidationError, ResourceNotFoundError)):
        logger.warning(log_message)
    elif isinstance(error, (AuthenticationError, AuthorizationError)):
        logger.warning(log_message, extra={"security": True})
    else:
        logger.error(log_message, exc_info=True)


async def handle_decisera_exception(request: Request, exc: DeciseraException) -> JSONResponse:
    """Exception handler for DeciseraException"""
    log_error(exc, request)
    
    error_response = format_error_response(exc, request)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Exception handler for HTTPException"""
    log_error(exc, request)
    
    error_response = format_error_response(exc, request)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """Exception handler for generic exceptions"""
    log_error(exc, request)
    
    # Don't expose internal errors in production
    from ..utils.config import settings
    include_trace = settings.debug_mode
    
    error_response = format_error_response(exc, request, include_trace)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


# Error utilities
def safe_get_dict(data: Dict, key: str, default: Any = None, required: bool = False):
    """
    Safely get value from dictionary with validation
    
    Args:
        data: Dictionary to get value from
        key: Key to retrieve
        default: Default value if key not found
        required: Whether the key is required
        
    Returns:
        Value from dictionary
        
    Raises:
        ValidationError: If required key is missing
    """
    if key not in data:
        if required:
            raise ValidationError(
                f"Missing required field: {key}",
                {"field": key}
            )
        return default
    
    return data[key]


def validate_required_fields(data: Dict, required_fields: list):
    """
    Validate that all required fields are present
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            {"missing_fields": missing_fields}
        )
