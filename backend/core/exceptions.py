
from .error_types import EnhancedError, ErrorFactory, ErrorType
from typing import Dict, List, Optional, Any


class UserError(Exception):
    """
    Exception raised for user-facing errors.
    This corresponds to Znova UserError.
    """
    def __init__(self, message, enhanced_error: Optional[EnhancedError] = None):
        self.message = message
        self.enhanced_error = enhanced_error or ErrorFactory.create_user_error(message)
        super().__init__(self.message)


class ValidationError(Exception):
    """
    Exception raised for validation errors.
    """
    def __init__(
        self, 
        message, 
        field_errors: Optional[Dict[str, str]] = None,
        enhanced_error: Optional[EnhancedError] = None
    ):
        self.message = message
        self.field_errors = field_errors or {}
        self.enhanced_error = enhanced_error or ErrorFactory.create_validation_error(
            message=message,
            field_errors=field_errors
        )
        super().__init__(self.message)


class AccessError(Exception):
    """
    Exception raised for access/permission errors.
    """
    def __init__(
        self, 
        message, 
        required_permission: Optional[str] = None,
        enhanced_error: Optional[EnhancedError] = None
    ):
        self.message = message
        self.required_permission = required_permission
        self.enhanced_error = enhanced_error or ErrorFactory.create_access_error(
            message=message,
            required_permission=required_permission
        )
        super().__init__(self.message)


class AuthenticationError(Exception):
    """
    Exception raised for authentication errors.
    """
    def __init__(self, message="Authentication failed", enhanced_error: Optional[EnhancedError] = None):
        self.message = message
        self.enhanced_error = enhanced_error or ErrorFactory.create_authentication_error(message)
        super().__init__(self.message)


class NetworkError(Exception):
    """
    Exception raised for network-related errors.
    """
    def __init__(self, message="Network error occurred", enhanced_error: Optional[EnhancedError] = None):
        self.message = message
        self.enhanced_error = enhanced_error or ErrorFactory.create_network_error(message)
        super().__init__(self.message)


class RateLimitError(Exception):
    """
    Exception raised for rate limiting errors.
    """
    def __init__(self, message="Rate limit exceeded", enhanced_error: Optional[EnhancedError] = None):
        self.message = message
        self.enhanced_error = enhanced_error or ErrorFactory.create_rate_limit_error(message)
        super().__init__(self.message)
