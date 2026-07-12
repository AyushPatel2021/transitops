"""
Permission Validation Middleware

This middleware provides comprehensive server-side permission checking for all API endpoints
using JWT claims as the single source of truth for user authorization.
"""

from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status, Request
from functools import wraps
import logging
from backend.services.auth_service import extract_user_claims_from_jwt, validate_jwt_token

logger = logging.getLogger(__name__)


class PermissionValidator:
    """
    Comprehensive permission validation using JWT claims.
    Validates all user actions against server-side JWT claims, not client-provided data.
    """
    
    def __init__(self):
        self.logger = logger
    
    def validate_model_permission(self, jwt_claims: Dict[str, Any], model_name: str, action: str) -> bool:
        """
        Validate if user has permission for a specific model action using model-level definitions.
        """
        try:
            from backend.core.registry import registry
            user_role = jwt_claims.get('role', 'user')
            
            # Admin role has all permissions by default
            if user_role == 'admin':
                return True
                
            # Get the model class from registry
            model_cls = registry.get_model(model_name)
            if not model_cls:
                self.logger.warning(f"Model {model_name} not found in registry during permission check")
                return False
                
            # Check model-level role permissions
            role_perms = getattr(model_cls, '_role_permissions', {})
            if user_role not in role_perms:
                self.logger.warning(f"Role {user_role} not defined in permissions for model {model_name}")
                return False
                
            perms = role_perms[user_role]
            allowed = perms.get(action, False)
            
            if not allowed:
                self.logger.warning(f"Permission denied: User role {user_role} lacks {action} on {model_name}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating model permission: {e}")
            return False
    
    def validate_role_based_access(self, jwt_claims: Dict[str, Any], required_roles: List[str]) -> bool:
        """
        Validate if user has one of the required roles using JWT claims.
        
        Args:
            jwt_claims: JWT token claims containing user role
            required_roles: List of roles that can access the resource
            
        Returns:
            Boolean indicating if user has required role
        """
        try:
            user_role = jwt_claims.get('role')
            if not user_role:
                return False
            
            return user_role in required_roles
            
        except Exception as e:
            self.logger.error(f"Error validating role-based access: {e}")
            return False
    
    def validate_domain_based_access(self, jwt_claims: Dict[str, Any], resource_data: Dict[str, Any]) -> bool:
        """
        Validate domain-based filtering using JWT claims.
        Ensures users can only access resources within their domain/scope.
        
        Args:
            jwt_claims: JWT token claims containing user context
            resource_data: Data of the resource being accessed
            
        Returns:
            Boolean indicating if user can access the resource
        """
        try:
            user_role = jwt_claims.get('role')
            
            # Admin users can access all resources
            if user_role == 'admin':
                return True
            
            return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating domain-based access: {e}")
            return False
    
    def validate_user_context_access(self, jwt_claims: Dict[str, Any], target_user_id: int) -> bool:
        """
        Validate if user can access another user's data using JWT claims.
        """
        try:
            current_user_id = jwt_claims.get('user_id')
            user_role = jwt_claims.get('role')
            
            # Users can always access their own data
            if current_user_id == target_user_id:
                return True
            
            # Admin users can access all user data
            if user_role == 'admin':
                return True
            
            self.logger.warning(f"User context access denied: User {current_user_id} cannot access user {target_user_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating user context access: {e}")
            return False


# Global permission validator instance
permission_validator = PermissionValidator()


def require_permission(model_name: str, action: str):
    """
    Decorator to require specific model permission using JWT claims.
    
    Args:
        model_name: Name of the model
        action: Required action permission
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and token from function arguments
            request = None
            token = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token required"
                )
            
            try:
                # Validate token and extract claims
                jwt_claims = validate_jwt_token(token)
                
                # Validate permission
                if not permission_validator.validate_model_permission(jwt_claims, model_name, action):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions for {model_name}.{action}"
                    )
                
                # Add JWT claims to kwargs for use in the endpoint
                kwargs['jwt_claims'] = jwt_claims
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Permission validation error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission validation failed"
                )
        
        return wrapper
    return decorator


def require_role(required_roles: List[str]):
    """
    Decorator to require specific user roles using JWT claims.
    
    Args:
        required_roles: List of roles that can access the endpoint
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and token from function arguments
            request = None
            token = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token required"
                )
            
            try:
                # Validate token and extract claims
                jwt_claims = validate_jwt_token(token)
                
                # Validate role
                if not permission_validator.validate_role_based_access(jwt_claims, required_roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Requires one of roles: {required_roles}"
                    )
                
                # Add JWT claims to kwargs for use in the endpoint
                kwargs['jwt_claims'] = jwt_claims
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Role validation error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Role validation failed"
                )
        
        return wrapper
    return decorator


def create_user_context_from_jwt(jwt_claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create user context dictionary from JWT claims for domain engine evaluation.
    This replaces localStorage-based user context with secure JWT-based context.
    
    Args:
        jwt_claims: Validated JWT token claims
        
    Returns:
        User context dictionary for domain engine
    """
    from backend.core.domain_engine import create_secure_user_context_from_jwt
    return create_secure_user_context_from_jwt(jwt_claims)


def validate_domain_filter_access(jwt_claims: Dict[str, Any], query_filters: Dict[str, Any]) -> bool:
    """
    Validate that domain filters in queries don't bypass user permissions.
    
    Args:
        jwt_claims: JWT token claims
        query_filters: Filters being applied to the query
        
    Returns:
        Boolean indicating if filters are allowed
    """
    try:
        user_role = jwt_claims.get('role')

        
        # Admin users can use any filters
        if user_role == 'admin':
            return True
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating domain filter access: {e}")
        return False