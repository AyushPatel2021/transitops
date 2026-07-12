"""
Enhanced error handler middleware for FastAPI with humorous error responses.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError
from typing import Union
import logging
import traceback

from .exceptions import (
    UserError, ValidationError, AccessError, AuthenticationError, 
    NetworkError, RateLimitError
)
from .error_types import ErrorFactory, ErrorType, ErrorSeverity

logger = logging.getLogger(__name__)


class EnhancedErrorHandler:
    """Enhanced error handler with humorous messages and detailed error information"""
    
    @staticmethod
    async def handle_user_error(request: Request, exc: UserError) -> JSONResponse:
        """Handle UserError exceptions"""
        logger.warning(f"UserError: {exc.message}")
        
        if exc.enhanced_error:
            error_data = exc.enhanced_error.to_dict()
        else:
            enhanced_error = ErrorFactory.create_user_error(exc.message)
            error_data = enhanced_error.to_dict()
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": exc.message,
                "error": error_data,
                "success": False
            }
        )
    
    @staticmethod
    async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle ValidationError exceptions"""
        logger.warning(f"ValidationError: {exc.message}")
        
        error_data = exc.enhanced_error.to_dict()
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.message,
                "error": error_data,
                "success": False
            }
        )
    
    @staticmethod
    async def handle_access_error(request: Request, exc: AccessError) -> JSONResponse:
        """Handle AccessError exceptions"""
        logger.warning(f"AccessError: {exc.message}")
        
        error_data = exc.enhanced_error.to_dict()
        
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": exc.message,
                "error": error_data,
                "success": False
            }
        )
    
    @staticmethod
    async def handle_authentication_error(request: Request, exc: AuthenticationError) -> JSONResponse:
        """Handle AuthenticationError exceptions"""
        logger.warning(f"AuthenticationError: {exc.message}")
        
        error_data = exc.enhanced_error.to_dict()
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": exc.message,
                "error": error_data,
                "success": False
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    @staticmethod
    async def handle_rate_limit_error(request: Request, exc: RateLimitError) -> JSONResponse:
        """Handle RateLimitError exceptions"""
        logger.warning(f"RateLimitError: {exc.message}")
        
        error_data = exc.enhanced_error.to_dict()
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": exc.message,
                "error": error_data,
                "success": False
            }
        )
    
    @staticmethod
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTPException with enhanced error information"""
        logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
        
        # Map HTTP status codes to error types
        error_type_map = {
            400: ErrorType.USER_ERROR,
            401: ErrorType.AUTHENTICATION_ERROR,
            403: ErrorType.PERMISSION_ERROR,
            404: ErrorType.NOT_FOUND_ERROR,
            422: ErrorType.VALIDATION_ERROR,
            429: ErrorType.RATE_LIMIT_ERROR,
            500: ErrorType.SERVER_ERROR,
        }
        
        error_type = error_type_map.get(exc.status_code, ErrorType.SERVER_ERROR)
        
        # Create enhanced error based on status code
        if exc.status_code == 400:
            enhanced_error = ErrorFactory.create_user_error(str(exc.detail))
        elif exc.status_code == 401:
            enhanced_error = ErrorFactory.create_authentication_error(str(exc.detail))
        elif exc.status_code == 403:
            enhanced_error = ErrorFactory.create_access_error(str(exc.detail))
        elif exc.status_code == 422:
            enhanced_error = ErrorFactory.create_validation_error(str(exc.detail))
        elif exc.status_code == 429:
            enhanced_error = ErrorFactory.create_rate_limit_error(str(exc.detail))
        elif exc.status_code == 404:
            enhanced_error = ErrorFactory.create_validation_error(
                str(exc.detail),
                suggestions=["Check the URL or resource ID", "Make sure the resource exists"]
            )
            enhanced_error.error_type = ErrorType.NOT_FOUND_ERROR
        else:
            enhanced_error = ErrorFactory.create_server_error(str(exc.detail))
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error": enhanced_error.to_dict(),
                "success": False
            }
        )
    
    @staticmethod
    async def handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle FastAPI request validation errors"""
        logger.warning(f"RequestValidationError: {exc.errors()}")
        
        # Extract field errors from pydantic validation errors
        field_errors = {}
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            field_errors[field_path] = error["msg"]
        
        enhanced_error = ErrorFactory.create_validation_error(
            "Request validation failed",
            field_errors=field_errors,
            suggestions=[
                "Check your request format",
                "Ensure all required fields are provided",
                "Verify data types match the expected format"
            ]
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request validation failed",
                "error": enhanced_error.to_dict(),
                "success": False
            }
        )
    
    @staticmethod
    async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
        """Handle SQLAlchemy integrity errors"""
        logger.error(f"IntegrityError: {str(exc)}")
        
        # Try to extract meaningful error message
        error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        
        # Common integrity error patterns
        if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg.lower():
            message = "This record already exists or conflicts with existing data"
            suggestions = [
                "Check if a similar record already exists",
                "Try using different values for unique fields",
                "Contact support if you believe this is an error"
            ]
        elif "FOREIGN KEY constraint failed" in error_msg or "foreign key" in error_msg.lower():
            message = "Referenced record does not exist or has been deleted"
            suggestions = [
                "Make sure all referenced records exist",
                "Check if related records have been deleted",
                "Refresh the page and try again"
            ]
        elif "NOT NULL constraint failed" in error_msg or "null value" in error_msg.lower():
            message = "Required information is missing"
            suggestions = [
                "Fill in all required fields",
                "Check for any missing mandatory information",
                "Ensure all form fields are properly completed"
            ]
        else:
            message = "Data integrity constraint violation"
            suggestions = [
                "Check your data for conflicts",
                "Ensure all relationships are valid",
                "Contact support if the problem persists"
            ]
        
        enhanced_error = ErrorFactory.create_validation_error(
            message,
            suggestions=suggestions
        )
        enhanced_error.error_type = ErrorType.DATA_INTEGRITY_ERROR
        enhanced_error.details = error_msg
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": message,
                "error": enhanced_error.to_dict(),
                "success": False
            }
        )
    
    @staticmethod
    async def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handle general SQLAlchemy errors"""
        logger.error(f"SQLAlchemyError: {str(exc)}")
        
        enhanced_error = ErrorFactory.create_server_error(
            "Database operation failed"
        )
        enhanced_error.details = str(exc)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Database operation failed",
                "error": enhanced_error.to_dict(),
                "success": False
            }
        )
    
    @staticmethod
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle any other unhandled exceptions"""
        logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        enhanced_error = ErrorFactory.create_server_error(
            "An unexpected error occurred"
        )
        enhanced_error.details = f"{type(exc).__name__}: {str(exc)}"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred",
                "error": enhanced_error.to_dict(),
                "success": False
            }
        )


def setup_error_handlers(app):
    """Setup all error handlers for the FastAPI app"""
    
    # Custom exception handlers
    app.add_exception_handler(UserError, EnhancedErrorHandler.handle_user_error)
    app.add_exception_handler(ValidationError, EnhancedErrorHandler.handle_validation_error)
    app.add_exception_handler(AccessError, EnhancedErrorHandler.handle_access_error)
    app.add_exception_handler(AuthenticationError, EnhancedErrorHandler.handle_authentication_error)
    app.add_exception_handler(RateLimitError, EnhancedErrorHandler.handle_rate_limit_error)
    
    # FastAPI built-in exception handlers
    app.add_exception_handler(HTTPException, EnhancedErrorHandler.handle_http_exception)
    app.add_exception_handler(RequestValidationError, EnhancedErrorHandler.handle_request_validation_error)
    
    # SQLAlchemy exception handlers
    app.add_exception_handler(IntegrityError, EnhancedErrorHandler.handle_integrity_error)
    app.add_exception_handler(SQLAlchemyError, EnhancedErrorHandler.handle_sqlalchemy_error)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, EnhancedErrorHandler.handle_generic_exception)
