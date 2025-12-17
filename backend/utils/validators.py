from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ValidationError, validator
import re

class ValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    
def validate_email(email: str) -> ValidationResult:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return ValidationResult(valid=True)
    return ValidationResult(valid=False, errors=["Invalid email format"])

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> ValidationResult:
    """Validate file has allowed extension."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext in allowed_extensions:
        return ValidationResult(valid=True)
    return ValidationResult(
        valid=False,
        errors=[f"File extension must be one of: {', '.join(allowed_extensions)}"]
    )

def validate_file_size(size_bytes: int, max_size_bytes: int) -> ValidationResult:
    """Validate file size is within limits."""
    if size_bytes <= max_size_bytes:
        return ValidationResult(valid=True)
    max_mb = max_size_bytes / (1024 * 1024)
    return ValidationResult(
        valid=False,
        errors=[f"File size exceeds maximum allowed size of {max_mb:.1f}MB"]
    )

def validate_dataset_name(name: str) -> ValidationResult:
    """Validate dataset name."""
    errors = []
    
    if len(name) < 3:
        errors.append("Dataset name must be at least 3 characters")
    if len(name) > 100:
        errors.append("Dataset name must not exceed 100 characters")
    if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
        errors.append("Dataset name can only contain letters, numbers, spaces, hyphens, and underscores")
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_model_config(config: Dict[str, Any]) -> ValidationResult:
    """Validate model training configuration."""
    errors = []
    
    required_fields = ['dataset_id', 'target_column', 'task_type']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    if 'task_type' in config:
        valid_tasks = ['classification', 'regression', 'clustering']
        if config['task_type'] not in valid_tasks:
            errors.append(f"task_type must be one of: {', '.join(valid_tasks)}")
    
    if 'model_types' in config:
        if not isinstance(config['model_types'], list) or len(config['model_types']) == 0:
            errors.append("model_types must be a non-empty list")
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_pagination_params(page: int, page_size: int, max_page_size: int = 100) -> ValidationResult:
    """Validate pagination parameters."""
    errors = []
    
    if page < 1:
        errors.append("page must be >= 1")
    if page_size < 1:
        errors.append("page_size must be >= 1")
    if page_size > max_page_size:
        errors.append(f"page_size must not exceed {max_page_size}")
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Trim to max length
    text = text[:max_length]
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text.strip()
