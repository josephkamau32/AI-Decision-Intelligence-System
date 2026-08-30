"""
Production Environment Validation and Checks
Validates configuration and dependencies on startup
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation check"""

    def __init__(self, passed: bool, message: str, severity: str = "error"):
        self.passed = passed
        self.message = message
        self.severity = severity  # error, warning, info


class ProductionValidator:
    """Validates production readiness"""

    def __init__(self):
        self.results: List[ValidationResult] = []

    def check_environment_variables(
        self, required_vars: List[str], optional_vars: List[str] = None
    ):
        """Check that required environment variables are set"""
        # Check required variables
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message=f"Required environment variable not set: {var}",
                        severity="error",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message=f"Environment variable set: {var}",
                        severity="info",
                    )
                )

        # Check optional variables
        if optional_vars:
            for var in optional_vars:
                value = os.getenv(var)
                if not value:
                    self.results.append(
                        ValidationResult(
                            passed=True,
                            message=f"Optional environment variable not set: {var}. Some features may be limited.",
                            severity="warning",
                        )
                    )

    def check_directory_permissions(self, directories: List[str]):
        """Check that required directories exist and are writable"""
        for dir_path in directories:
            path = Path(dir_path)

            # Check if directory exists
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.results.append(
                        ValidationResult(
                            passed=True,
                            message=f"Created directory: {dir_path}",
                            severity="info",
                        )
                    )
                except Exception as e:
                    self.results.append(
                        ValidationResult(
                            passed=False,
                            message=f"Cannot create directory {dir_path}: {e}",
                            severity="error",
                        )
                    )
                    continue

            # Check if directory is writable
            if not os.access(path, os.W_OK):
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message=f"Directory not writable: {dir_path}",
                        severity="error",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message=f"Directory writable: {dir_path}",
                        severity="info",
                    )
                )

    def check_python_version(self, min_version: tuple = (3, 8)):
        """Check Python version meets minimum requirements"""
        current_version = sys.version_info[:2]

        if current_version < min_version:
            self.results.append(
                ValidationResult(
                    passed=False,
                    message=f"Python version {current_version[0]}.{current_version[1]} is below minimum {min_version[0]}.{min_version[1]}",
                    severity="error",
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    passed=True,
                    message=f"Python version {current_version[0]}.{current_version[1]} meets requirements",
                    severity="info",
                )
            )

    def check_dependencies(self, critical_imports: List[str]):
        """Check that critical dependencies can be imported"""
        for module_name in critical_imports:
            try:
                __import__(module_name)
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message=f"Dependency available: {module_name}",
                        severity="info",
                    )
                )
            except ImportError as e:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message=f"Missing critical dependency: {module_name} - {e}",
                        severity="error",
                    )
                )

    def check_optional_dependencies(self, optional_imports: List[str]):
        """Check optional dependencies (warnings only)"""
        for module_name in optional_imports:
            try:
                __import__(module_name)
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message=f"Optional dependency available: {module_name}",
                        severity="info",
                    )
                )
            except ImportError:
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message=f"Optional dependency not available: {module_name}. Some features may be disabled.",
                        severity="warning",
                    )
                )

    def check_disk_space(self, min_mb: int = 1000):
        """Check available disk space"""
        try:
            import shutil

            stats = shutil.disk_usage(os.getcwd())
            free_mb = stats.free / (1024 * 1024)

            if free_mb < min_mb:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message=f"Low disk space: {free_mb:.0f}MB available, {min_mb}MB recommended",
                        severity="warning",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message=f"Disk space OK: {free_mb:.0f}MB available",
                        severity="info",
                    )
                )
        except Exception as e:
            self.results.append(
                ValidationResult(
                    passed=True,
                    message=f"Could not check disk space: {e}",
                    severity="warning",
                )
            )

    def check_security_settings(self, settings_obj):
        """Check security-related settings"""
        # Check SECRET_KEY
        if hasattr(settings_obj, "secret_key"):
            if len(settings_obj.secret_key) < 32:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message="SECRET_KEY is too short (minimum 32 characters)",
                        severity="error",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message="SECRET_KEY length is adequate",
                        severity="info",
                    )
                )

        # Check DEBUG mode in production
        if hasattr(settings_obj, "debug_mode"):
            if settings_obj.debug_mode and os.getenv("ENVIRONMENT") == "production":
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message="DEBUG mode is enabled in production environment",
                        severity="error",
                    )
                )

        # Check CORS settings
        if hasattr(settings_obj, "allowed_origins"):
            if (
                "*" in settings_obj.allowed_origins
                and os.getenv("ENVIRONMENT") == "production"
            ):
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message="CORS allows all origins (*) in production environment",
                        severity="warning",
                    )
                )

    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        errors = [r for r in self.results if not r.passed and r.severity == "error"]
        warnings = [r for r in self.results if r.severity == "warning"]

        return {
            "total_checks": len(self.results),
            "passed": len([r for r in self.results if r.passed]),
            "errors": len(errors),
            "warnings": len(warnings),
            "error_messages": [r.message for r in errors],
            "warning_messages": [r.message for r in warnings],
        }

    def print_summary(self):
        """Print validation summary to console"""
        summary = self.get_summary()

        print("\n" + "=" * 70)
        print("PRODUCTION READINESS VALIDATION")
        print("=" * 70)

        for result in self.results:
            if result.severity == "error" and not result.passed:
                print(f"❌ ERROR: {result.message}")
            elif result.severity == "warning":
                print(f"⚠️  WARNING: {result.message}")

        print("\n" + "-" * 70)
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Passed: {summary['passed']}")
        print(f"Errors: {summary['errors']}")
        print(f"Warnings: {summary['warnings']}")
        print("=" * 70 + "\n")

        return summary["errors"] == 0


def run_startup_validation():
    """Run all startup validation checks"""
    from .config import settings

    validator = ProductionValidator()

    # Check Python version
    validator.check_python_version(min_version=(3, 8))

    # Check critical dependencies
    validator.check_dependencies(["fastapi", "uvicorn", "pydantic", "jose", "passlib"])

    # Check optional dependencies
    validator.check_optional_dependencies(
        ["pandas", "sklearn", "mlflow", "langchain", "google.generativeai"]
    )

    # Check required directories
    validator.check_directory_permissions(
        [settings.upload_dir, "mlops/experiments", "storage"]
    )

    # Check optional environment variables (API keys)
    validator.check_environment_variables(
        required_vars=[],  # No strictly required vars for basic operation
        optional_vars=["GOOGLE_API_KEY", "OPENAI_API_KEY", "DATABASE_URL"],
    )

    # Check security settings
    validator.check_security_settings(settings)

    # Check disk space
    validator.check_disk_space(min_mb=500)

    # Print summary
    is_valid = validator.print_summary()

    return is_valid, validator


if __name__ == "__main__":
    # Run validation when executed directly
    is_valid, validator = run_startup_validation()

    if not is_valid:
        print("⚠️  Production validation failed. Please fix the errors above.")
        sys.exit(1)
    else:
        print("✅ Production validation passed!")
        sys.exit(0)
