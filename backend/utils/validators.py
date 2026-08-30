from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ValidationError, validator
import re


class ValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []


def validate_email(email: str) -> ValidationResult:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, email):
        return ValidationResult(valid=True)
    return ValidationResult(valid=False, errors=["Invalid email format"])


def validate_file_extension(
    filename: str, allowed_extensions: List[str]
) -> ValidationResult:
    """Validate file has allowed extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in allowed_extensions:
        return ValidationResult(valid=True)
    return ValidationResult(
        valid=False,
        errors=[f"File extension must be one of: {', '.join(allowed_extensions)}"],
    )


def validate_file_size(size_bytes: int, max_size_bytes: int) -> ValidationResult:
    """Validate file size is within limits."""
    if size_bytes <= max_size_bytes:
        return ValidationResult(valid=True)
    max_mb = max_size_bytes / (1024 * 1024)
    return ValidationResult(
        valid=False,
        errors=[f"File size exceeds maximum allowed size of {max_mb:.1f}MB"],
    )


def validate_dataset_name(name: str) -> ValidationResult:
    """Validate dataset name."""
    errors = []

    if len(name) < 3:
        errors.append("Dataset name must be at least 3 characters")
    if len(name) > 100:
        errors.append("Dataset name must not exceed 100 characters")
    if not re.match(r"^[a-zA-Z0-9\s_-]+$", name):
        errors.append(
            "Dataset name can only contain letters, numbers, spaces, hyphens, and underscores"
        )

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_model_config(config: Dict[str, Any]) -> ValidationResult:
    """Validate model training configuration."""
    errors = []

    required_fields = ["dataset_id", "target_column", "task_type"]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    if "task_type" in config:
        valid_tasks = ["classification", "regression", "clustering"]
        if config["task_type"] not in valid_tasks:
            errors.append(f"task_type must be one of: {', '.join(valid_tasks)}")

    if "model_types" in config:
        if (
            not isinstance(config["model_types"], list)
            or len(config["model_types"]) == 0
        ):
            errors.append("model_types must be a non-empty list")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_pagination_params(
    page: int, page_size: int, max_page_size: int = 100
) -> ValidationResult:
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
    text = text.replace("\x00", "")

    # Trim to max length
    text = text[:max_length]

    # Remove dangerous patterns
    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    return text.strip()


def validate_password_strength(password: str) -> ValidationResult:
    """
    Validate password meets security requirements.
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    # Check for common weak passwords
    common_passwords = ["password", "12345678", "qwerty", "admin", "letmein"]
    if password.lower() in common_passwords:
        errors.append("Password is too common. Please choose a stronger password")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def detect_sql_injection(text: str) -> ValidationResult:
    """Detect potential SQL injection attempts."""
    sql_patterns = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(--|\#|\/\*)",
        r"(\bEXEC\b|\bEXECUTE\b)",
        r"(\';|\";\s*--)",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return ValidationResult(
                valid=False, errors=["Potential SQL injection detected"]
            )

    return ValidationResult(valid=True)


def validate_file_content_type(
    content_type: str, allowed_types: List[str]
) -> ValidationResult:
    """Validate file content type."""
    if content_type in allowed_types:
        return ValidationResult(valid=True)

    return ValidationResult(
        valid=False, errors=[f"Content type must be one of: {', '.join(allowed_types)}"]
    )


def validate_json_structure(
    data: Dict[str, Any], required_keys: List[str]
) -> ValidationResult:
    """Validate JSON structure has required keys."""
    errors = []

    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        errors.append(f"Missing required keys: {', '.join(missing_keys)}")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_url(url: str) -> ValidationResult:
    """Validate URL format."""
    url_pattern = r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"

    if re.match(url_pattern, url):
        return ValidationResult(valid=True)

    return ValidationResult(valid=False, errors=["Invalid URL format"])


def validate_api_key_format(api_key: str) -> ValidationResult:
    """Validate API key format."""
    errors = []

    if len(api_key) < 20:
        errors.append("API key too short")

    if not re.match(r"^[a-zA-Z0-9_-]+$", api_key):
        errors.append("API key contains invalid characters")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_csv_headers(headers: List[str]) -> ValidationResult:
    """Validate CSV headers are valid."""
    errors = []

    if not headers:
        errors.append("CSV file must have headers")

    # Check for duplicate headers
    if len(headers) != len(set(headers)):
        errors.append("CSV file contains duplicate headers")

    # Check header naming
    for header in headers:
        if not header or not header.strip():
            errors.append("CSV contains empty header names")
            break
        if not re.match(r"^[a-zA-Z0-9_\s-]+$", header):
            errors.append(f"Invalid header name: {header}")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_numeric_range(
    value: float, min_val: Optional[float] = None, max_val: Optional[float] = None
) -> ValidationResult:
    """Validate numeric value is within range."""
    errors = []

    if min_val is not None and value < min_val:
        errors.append(f"Value {value} is below minimum {min_val}")

    if max_val is not None and value > max_val:
        errors.append(f"Value {value} exceeds maximum {max_val}")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Remove any path components
    filename = filename.split("/")[-1].split("\\")[-1]

    # Remove dangerous characters
    filename = re.sub(r"[^\w\s.-]", "", filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip().strip(".")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")

    return filename or "unnamed_file"
