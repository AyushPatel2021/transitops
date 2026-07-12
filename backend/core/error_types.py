"""
Enhanced error handling system with different error types and humorous messages.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
import random


class ErrorType(Enum):
    """Different types of errors with their characteristics"""
    USER_ERROR = "user_error"
    VALIDATION_ERROR = "validation_error"
    ACCESS_ERROR = "access_error"
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    NOT_FOUND_ERROR = "not_found_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    AUTHENTICATION_ERROR = "authentication_error"
    PERMISSION_ERROR = "permission_error"
    DATA_INTEGRITY_ERROR = "data_integrity_error"


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HumorousErrorMessages:
    """Collection of humorous error messages for different error types"""
    
    USER_ERROR_MESSAGES = [
        "Oops! Looks like someone's having a case of the Mondays! 🤦‍♂️",
        "Well, that didn't go as planned... Time for Plan B! 🎭",
        "Houston, we have a problem... but it's totally fixable! 🚀",
        "Whoopsie-daisy! Let's try that again, shall we? 🌼",
        "Error 404: Your luck seems to be temporarily unavailable! 🍀",
        "That's not quite right... but hey, practice makes perfect! 🎯",
        "Looks like we hit a tiny speed bump on the road to success! 🛣️"
    ]
    
    VALIDATION_ERROR_MESSAGES = [
        "Your data is playing hard to get! Let's make it happy! 💕",
        "Validation says 'Nope!' - but we can fix this together! ✋",
        "The form police have some concerns about your input! 👮‍♂️",
        "Your data needs a little TLC before it can proceed! 🛠️",
        "Looks like some fields are feeling a bit neglected! 🥺",
        "The validation fairy is being extra picky today! 🧚‍♀️",
        "Your input is 99% perfect - let's get that last 1%! 📊"
    ]
    
    ACCESS_ERROR_MESSAGES = [
        "Access denied! You shall not pass... without proper permissions! 🧙‍♂️",
        "This area is VIP only - time to upgrade your membership! 💎",
        "Looks like you're trying to peek behind the curtain! 🎭",
        "Sorry, this feature is playing hard to get! 💅",
        "You need the secret handshake for this one! 🤝",
        "This content is more exclusive than a celebrity party! 🌟",
        "Access level: Not quite there yet, but you're awesome anyway! 🎖️"
    ]
    
    NETWORK_ERROR_MESSAGES = [
        "The internet seems to be taking a coffee break! ☕",
        "Network gremlins are at it again! 👹",
        "Your connection is playing hide and seek! 🙈",
        "The tubes of the internet are a bit clogged right now! 🚰",
        "Looks like the WiFi is having commitment issues! 📶",
        "The network is being a bit moody today! 😤",
        "Connection timeout: Even computers need a breather sometimes! 💨"
    ]
    
    SERVER_ERROR_MESSAGES = [
        "Our server is having an existential crisis! 🤖",
        "Something went wrong in the digital realm! ⚡",
        "The server hamsters need a quick snack break! 🐹",
        "Our backend is doing its best impression of a confused penguin! 🐧",
        "Error 500: The server is temporarily speaking in tongues! 👅",
        "The digital gods are not pleased... but we're working on it! ⚡",
        "Our server just blue-screened... metaphorically speaking! 💙"
    ]
    
    NOT_FOUND_MESSAGES = [
        "404: This page went on vacation and forgot to leave a note! 🏖️",
        "We looked everywhere, but this content is playing hide and seek! 🔍",
        "This page has vanished like socks in a washing machine! 🧦",
        "Error 404: Content not found, but your sense of humor is intact! 😄",
        "This page is more elusive than a unicorn! 🦄",
        "We've searched high and low, but this content is MIA! 🕵️‍♂️",
        "This page decided to take an unscheduled vacation! ✈️"
    ]
    
    RATE_LIMIT_MESSAGES = [
        "Whoa there, speed racer! Let's take it down a notch! 🏎️",
        "You're moving faster than a caffeinated cheetah! ☕🐆",
        "Slow down, turbo! Even The Flash takes breaks! ⚡",
        "Easy there, tiger! Rome wasn't built in a day! 🏛️",
        "You're clicking faster than a woodpecker! 🐦",
        "Pump the brakes! Even race cars need pit stops! 🏁",
        "Hold your horses! Good things come to those who wait! 🐎"
    ]
    
    AUTHENTICATION_MESSAGES = [
        "Who goes there? State your name and password! 🛡️",
        "Authentication failed: Are you who you say you are? 🕵️‍♂️",
        "Login error: Your credentials are having an identity crisis! 🎭",
        "Access denied: You're not on the guest list! 📋",
        "Authentication timeout: Your session went for a walk! 🚶‍♂️",
        "Login failed: Time to refresh those memory banks! 🧠",
        "Credentials rejected: Even computers have trust issues! 🤖"
    ]
    
    PERMISSION_MESSAGES = [
        "Permission denied: You need the golden ticket for this! 🎫",
        "Access restricted: This feature is for VIPs only! 👑",
        "Insufficient privileges: Time to level up! 🎮",
        "Permission error: You're not the chosen one... yet! ⚡",
        "Access denied: This area requires special clearance! 🔐",
        "Unauthorized: You need the magic words! ✨",
        "Permission denied: Your access card needs an upgrade! 💳"
    ]
    
    DATA_INTEGRITY_MESSAGES = [
        "Data integrity error: Your data is having an identity crisis! 🎭",
        "Constraint violation: The database is being extra picky! 🤓",
        "Data conflict: Your information is arguing with itself! 🥊",
        "Integrity check failed: The data police found an issue! 👮‍♂️",
        "Constraint error: The database has some strong opinions! 💪",
        "Data validation failed: Your info needs a reality check! ✅",
        "Integrity violation: The data is not playing by the rules! 📏"
    ]

    @classmethod
    def get_random_message(cls, error_type: ErrorType) -> str:
        """Get a random humorous message for the given error type"""
        message_map = {
            ErrorType.USER_ERROR: cls.USER_ERROR_MESSAGES,
            ErrorType.VALIDATION_ERROR: cls.VALIDATION_ERROR_MESSAGES,
            ErrorType.ACCESS_ERROR: cls.ACCESS_ERROR_MESSAGES,
            ErrorType.NETWORK_ERROR: cls.NETWORK_ERROR_MESSAGES,
            ErrorType.SERVER_ERROR: cls.SERVER_ERROR_MESSAGES,
            ErrorType.NOT_FOUND_ERROR: cls.NOT_FOUND_MESSAGES,
            ErrorType.RATE_LIMIT_ERROR: cls.RATE_LIMIT_MESSAGES,
            ErrorType.AUTHENTICATION_ERROR: cls.AUTHENTICATION_MESSAGES,
            ErrorType.PERMISSION_ERROR: cls.PERMISSION_MESSAGES,
            ErrorType.DATA_INTEGRITY_ERROR: cls.DATA_INTEGRITY_MESSAGES,
        }
        
        messages = message_map.get(error_type, cls.USER_ERROR_MESSAGES)
        return random.choice(messages)


class EnhancedError:
    """Enhanced error class with humor and detailed information"""
    
    def __init__(
        self,
        error_type: ErrorType,
        title: str,
        message: str,
        details: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        humorous_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        field_errors: Optional[Dict[str, str]] = None
    ):
        self.error_type = error_type
        self.title = title
        self.message = message
        self.details = details
        self.severity = severity
        self.humorous_message = humorous_message or HumorousErrorMessages.get_random_message(error_type)
        self.suggestions = suggestions or []
        self.error_code = error_code
        self.field_errors = field_errors or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API response"""
        return {
            "error_type": self.error_type.value,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "severity": self.severity.value,
            "humorous_message": self.humorous_message,
            "suggestions": self.suggestions,
            "error_code": self.error_code,
            "field_errors": self.field_errors,
            "show_dialog": True  # Always show dialog for enhanced errors
        }


class ErrorFactory:
    """Factory class to create different types of errors"""
    
    @staticmethod
    def create_user_error(
        message: str,
        suggestions: Optional[List[str]] = None
    ) -> EnhancedError:
        """Create a user error"""
        default_suggestions = [
            "Double-check your input",
            "Try a different approach", 
            "Contact support if you need help"
        ]
        
        return EnhancedError(
            error_type=ErrorType.USER_ERROR,
            title="User Error",
            message=message,
            severity=ErrorSeverity.WARNING,
            suggestions=suggestions or default_suggestions,
            error_code="USER_ERROR"
        )
    
    @staticmethod
    def create_validation_error(
        message: str,
        field_errors: Optional[Dict[str, str]] = None,
        suggestions: Optional[List[str]] = None
    ) -> EnhancedError:
        """Create a validation error"""
        default_suggestions = [
            "Double-check your input values",
            "Make sure all required fields are filled",
            "Check for any special character restrictions"
        ]
        
        return EnhancedError(
            error_type=ErrorType.VALIDATION_ERROR,
            title="Validation Error",
            message=message,
            severity=ErrorSeverity.WARNING,
            suggestions=suggestions or default_suggestions,
            field_errors=field_errors,
            error_code="VALIDATION_FAILED"
        )
    
    @staticmethod
    def create_access_error(
        message: str,
        required_permission: Optional[str] = None
    ) -> EnhancedError:
        """Create an access error"""
        suggestions = ["Contact your administrator for access"]
        if required_permission:
            suggestions.append(f"You need '{required_permission}' permission")
        
        return EnhancedError(
            error_type=ErrorType.ACCESS_ERROR,
            title="Access Denied",
            message=message,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions,
            error_code="ACCESS_DENIED"
        )
    
    @staticmethod
    def create_authentication_error(
        message: str = "Authentication failed"
    ) -> EnhancedError:
        """Create an authentication error"""
        return EnhancedError(
            error_type=ErrorType.AUTHENTICATION_ERROR,
            title="Authentication Required",
            message=message,
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check your username and password",
                "Try logging out and logging back in",
                "Contact support if the problem persists"
            ],
            error_code="AUTH_FAILED"
        )
    
    @staticmethod
    def create_server_error(
        message: str = "An unexpected error occurred"
    ) -> EnhancedError:
        """Create a server error"""
        return EnhancedError(
            error_type=ErrorType.SERVER_ERROR,
            title="Server Error",
            message=message,
            severity=ErrorSeverity.CRITICAL,
            suggestions=[
                "Try refreshing the page",
                "Wait a moment and try again",
                "Contact support if the issue persists"
            ],
            error_code="SERVER_ERROR"
        )
    
    @staticmethod
    def create_network_error(
        message: str = "Network connection failed"
    ) -> EnhancedError:
        """Create a network error"""
        return EnhancedError(
            error_type=ErrorType.NETWORK_ERROR,
            title="Connection Error",
            message=message,
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check your internet connection",
                "Try refreshing the page",
                "Wait a moment and try again"
            ],
            error_code="NETWORK_ERROR"
        )
    
    @staticmethod
    def create_rate_limit_error(
        message: str = "Too many requests"
    ) -> EnhancedError:
        """Create a rate limit error"""
        return EnhancedError(
            error_type=ErrorType.RATE_LIMIT_ERROR,
            title="Rate Limit Exceeded",
            message=message,
            severity=ErrorSeverity.WARNING,
            suggestions=[
                "Wait a moment before trying again",
                "Slow down your requests",
                "Try again in a few minutes"
            ],
            error_code="RATE_LIMIT"
        )