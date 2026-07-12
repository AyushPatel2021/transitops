"""
Domain Expression Engine

This module provides parsing and evaluation of domain expressions for conditional
field visibility and readonly states. Domain expressions support both simple and
complex logical operations with an intuitive syntax.

The domain engine now uses secure JWT-based user context instead of localStorage-based
user data to prevent client-side manipulation of user permissions and roles.

Example domain expressions:
Simple (implicit AND):
- "[('status', '=', 'draft')]"
- "[('amount', '>', 100), ('state', 'in', ['pending', 'approved'])]"

Complex with explicit logical operators:

- "[[('amount', '>', 1000)], '&', [('status', '=', 'active'), ('priority', '=', 'high')]]"
  Means: (amount > 1000) AND (status = 'active' AND priority = 'high')

Security Note:
All user context data is now derived from server-validated JWT tokens, ensuring that
user roles, permissions, and other sensitive data cannot be tampered with on the client side.
"""

import ast
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date

logger = logging.getLogger(__name__)


@dataclass
class DomainCondition:
    """Represents a single domain condition like ('field', '=', 'value')"""
    field: str
    operator: str
    value: Any
    
    def __str__(self):
        return f"('{self.field}', '{self.operator}', {repr(self.value)})"


@dataclass
class DomainGroup:
    """Represents a group of conditions with implicit AND logic"""
    conditions: List[DomainCondition]
    
    def __str__(self):
        return " AND ".join(str(cond) for cond in self.conditions)


@dataclass
class DomainAST:
    """Abstract Syntax Tree for domain expressions"""
    groups: List[DomainGroup]
    operators: List[str]  # Logical operators between groups ('&' for AND, '|' for OR)
    
    def __str__(self):
        if len(self.groups) == 1:
            return str(self.groups[0])
        
        result = str(self.groups[0])
        for i, op in enumerate(self.operators):
            op_symbol = " OR " if op == "|" else " AND "
            result += op_symbol + str(self.groups[i + 1])
        return f"({result})"


@dataclass
class ValidationResult:
    """Result of domain expression validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class DomainParseError(Exception):
    """Raised when domain expression parsing fails"""
    pass


class DomainEvaluationError(Exception):
    """Raised when domain expression evaluation fails"""
    pass


class DomainEngine:
    """
    Enhanced domain expression parser and evaluator with secure JWT-based user context.
    
    Supports both simple and complex domain expressions:
    
    Simple format (implicit AND):
    - "[('field', '=', 'value')]" 
    - "[('field1', '=', 'value1'), ('field2', '>', 100)]"
    
    Complex format with explicit logical operators:
    - "[[('field1', '=', 'value1'), ('field2', '>', 100)], '|', ('field3', '!=', False)]"
    - "[[('status', '=', 'active')], '&', [('priority', '=', 'high'), ('amount', '>', 1000)]]"
    
    Operators: =, !=, <, >, <=, >=, in, not in, like, ilike
    Logical: & (AND), | (OR)
    
    Security Features:
    - Validates user_context comes from JWT tokens, not localStorage
    - Prevents client-side manipulation of user roles and permissions
    - Logs security violations for audit purposes
    """
    
    SUPPORTED_OPERATORS = {
        '=', '!=', '<', '>', '<=', '>=', 
        'in', 'not in', 'like', 'ilike'
    }
    
    LOGICAL_OPERATORS = {'&', '|'}
    
    def __init__(self):
        self.logger = logger
    
    def validate_secure_user_context(self, user_context: Dict[str, Any]) -> bool:
        """
        Validate that user_context comes from secure JWT source, not localStorage.
        
        This method ensures that user context contains the expected structure
        from JWT claims and logs any security violations.
        
        Args:
            user_context: User context dictionary to validate
            
        Returns:
            Boolean indicating if user context is valid and secure
        """
        if not user_context:
            self.logger.warning("Domain engine: Empty user_context provided")
            return False
        
        # Check for JWT source marker (security feature)
        if user_context.get('_source') != 'jwt':
            self.logger.warning("Domain engine: user_context missing JWT source marker - possible localStorage usage")
            return False
        
        # Check for required JWT-based fields
        required_fields = ['id', 'email', 'role']
        for field in required_fields:
            if field not in user_context:
                self.logger.warning(f"Domain engine: Missing required field '{field}' in user_context")
                return False
        
        # Validate role structure (should come from JWT)
        role_data = user_context.get('role')
        if not isinstance(role_data, dict) or 'name' not in role_data:
            self.logger.warning("Domain engine: Invalid role structure in user_context")
            return False
        
        # Log successful validation for audit
        self.logger.debug(f"Domain engine: Validated secure user_context for user {user_context.get('email')}")
        return True
    
    def parse_expression(self, expression: str) -> DomainAST:
        """
        Parse a domain expression string into a DomainAST.
        
        Supports both simple and complex formats:
        Simple: "[('field', '=', 'value'), ('field2', '>', 100)]" (implicit AND)
        Complex: "[[('field1', '=', 'value1')], '|', [('field2', '>', 100)]]" (explicit operators)
        
        Args:
            expression: Domain expression string
            
        Returns:
            DomainAST object representing the parsed expression
            
        Raises:
            DomainParseError: If the expression cannot be parsed
        """
        if not expression or not expression.strip():
            return DomainAST(groups=[], operators=[])
        
        try:
            # Remove whitespace and validate basic structure
            expr = expression.strip()
            if not (expr.startswith('[') and expr.endswith(']')):
                raise DomainParseError(f"Domain expression must be wrapped in brackets: {expression}")
            
            # Use ast.literal_eval for safe parsing
            parsed = ast.literal_eval(expr)
            
            if not isinstance(parsed, list):
                raise DomainParseError(f"Domain expression must be a list: {expression}")
            
            # Check if this is a complex format (contains nested lists and operators)
            has_nested_lists = any(isinstance(item, list) for item in parsed)
            has_operators = any(isinstance(item, str) and item in self.LOGICAL_OPERATORS for item in parsed)
            
            if has_nested_lists or has_operators:
                return self._parse_complex_expression(parsed, expression)
            else:
                return self._parse_simple_expression(parsed, expression)
                
        except (ValueError, SyntaxError) as e:
            raise DomainParseError(f"Invalid domain expression syntax: {expression}. Error: {str(e)}")
        except Exception as e:
            raise DomainParseError(f"Failed to parse domain expression: {expression}. Error: {str(e)}")
    
    def _parse_simple_expression(self, parsed: List, original_expr: str) -> DomainAST:
        """Parse simple format: [('field', '=', 'value'), ('field2', '>', 100)]"""
        conditions = []
        
        for item in parsed:
            if not isinstance(item, (list, tuple)) or len(item) != 3:
                raise DomainParseError(f"Each condition must be a 3-tuple (field, operator, value): {item}")
            
            field, operator, value = item
            
            if not isinstance(field, str):
                raise DomainParseError(f"Field name must be a string: {field}")
            
            if not isinstance(operator, str) or operator not in self.SUPPORTED_OPERATORS:
                raise DomainParseError(f"Unsupported operator '{operator}'. Supported: {self.SUPPORTED_OPERATORS}")
            
            conditions.append(DomainCondition(field=field, operator=operator, value=value))
        
        # Simple format has one group with implicit AND
        group = DomainGroup(conditions=conditions)
        return DomainAST(groups=[group], operators=[])
    
    def _parse_complex_expression(self, parsed: List, original_expr: str) -> DomainAST:
        """Parse complex format: [[('field1', '=', 'value1')], '|', [('field2', '>', 100)]]"""
        groups = []
        operators = []
        
        i = 0
        while i < len(parsed):
            item = parsed[i]
            
            if isinstance(item, str) and item in self.LOGICAL_OPERATORS:
                operators.append(item)
                i += 1
            elif isinstance(item, list):
                # Parse this group of conditions
                conditions = []
                for condition_item in item:
                    if not isinstance(condition_item, (list, tuple)) or len(condition_item) != 3:
                        raise DomainParseError(f"Each condition must be a 3-tuple (field, operator, value): {condition_item}")
                    
                    field, operator, value = condition_item
                    
                    if not isinstance(field, str):
                        raise DomainParseError(f"Field name must be a string: {field}")
                    
                    if not isinstance(operator, str) or operator not in self.SUPPORTED_OPERATORS:
                        raise DomainParseError(f"Unsupported operator '{operator}'. Supported: {self.SUPPORTED_OPERATORS}")
                    
                    conditions.append(DomainCondition(field=field, operator=operator, value=value))
                
                groups.append(DomainGroup(conditions=conditions))
                i += 1
            elif isinstance(item, tuple) and len(item) == 3:
                # Single condition not wrapped in a list - treat as a single-condition group
                field, operator, value = item
                
                if not isinstance(field, str):
                    raise DomainParseError(f"Field name must be a string: {field}")
                
                if not isinstance(operator, str) or operator not in self.SUPPORTED_OPERATORS:
                    raise DomainParseError(f"Unsupported operator '{operator}'. Supported: {self.SUPPORTED_OPERATORS}")
                
                condition = DomainCondition(field=field, operator=operator, value=value)
                groups.append(DomainGroup(conditions=[condition]))
                i += 1
            else:
                raise DomainParseError(f"Invalid item in complex expression: {item}")
        
        # Validate that we have the right number of operators
        if len(operators) != len(groups) - 1:
            raise DomainParseError(f"Number of operators ({len(operators)}) must be one less than number of groups ({len(groups)})")
        
        return DomainAST(groups=groups, operators=operators)
    
    def evaluate(self, expression: str, context: Dict[str, Any], user_context: Dict[str, Any] = None) -> bool:
        """
        Evaluate a domain expression against a context (form data) and secure user context.
        
        Args:
            expression: Domain expression string
            context: Dictionary containing field values
            user_context: Dictionary containing user information from JWT claims (secure)
            
        Returns:
            Boolean result of the expression evaluation
            
        Raises:
            DomainEvaluationError: If evaluation fails or user_context is insecure
        """
        try:
            if not expression or not expression.strip():
                return True  # Empty expression is always true (show field)
            
            # Validate user_context security if provided
            if user_context and not self.validate_secure_user_context(user_context):
                self.logger.error("Domain engine: Insecure user_context detected, rejecting evaluation")
                raise DomainEvaluationError("Invalid user context - must come from JWT claims")
            
            domain_ast = self.parse_expression(expression)
            
            if not domain_ast.groups:
                return True  # No groups means always true
            
            # Evaluate each group (groups have implicit AND between conditions)
            group_results = []
            for group in domain_ast.groups:
                group_result = self._evaluate_group(group, context, user_context)
                group_results.append(group_result)
            
            # Apply logical operators between groups
            if not domain_ast.operators:
                # Single group or no operators - return the first (and only) result
                return group_results[0] if group_results else True
            
            # Apply operators left to right
            result = group_results[0]
            for i, operator in enumerate(domain_ast.operators):
                next_result = group_results[i + 1]
                if operator == '|':  # OR
                    result = result or next_result
                elif operator == '&':  # AND
                    result = result and next_result
                else:
                    self.logger.warning(f"Unknown logical operator '{operator}', treating as AND")
                    result = result and next_result
            
            return result
                
        except DomainParseError as e:
            self.logger.error(f"Domain parse error: {e}")
            raise DomainEvaluationError(f"Parse error: {e}")
        except Exception as e:
            self.logger.error(f"Domain evaluation error: {e}")
            raise DomainEvaluationError(f"Evaluation error: {e}")
    
    def _evaluate_group(self, group: DomainGroup, context: Dict[str, Any], user_context: Dict[str, Any] = None) -> bool:
        """
        Evaluate a group of conditions (implicit AND between conditions).
        
        Args:
            group: DomainGroup to evaluate
            context: Field values context
            user_context: User information context
            
        Returns:
            Boolean result of the group (all conditions must be true)
        """
        if not group.conditions:
            return True
        
        results = []
        for condition in group.conditions:
            result = self._evaluate_condition(condition, context, user_context)
            results.append(result)
        
        # All conditions in a group must be true (implicit AND)
        return all(results)
    
    def _evaluate_condition(self, condition: DomainCondition, context: Dict[str, Any], user_context: Dict[str, Any] = None) -> bool:
        """
        Evaluate a single domain condition.
        
        Args:
            condition: DomainCondition to evaluate
            context: Field values context
            user_context: User information context
            
        Returns:
            Boolean result of the condition
        """
        field_value = self._get_field_value(condition.field, context, user_context)
        expected_value = condition.value
        operator = condition.operator
        
        try:
            # Handle different operators
            if operator == '=':
                return self._compare_equal(field_value, expected_value)
            elif operator == '!=':
                return not self._compare_equal(field_value, expected_value)
            elif operator == '<':
                return self._compare_less_than(field_value, expected_value)
            elif operator == '>':
                return self._compare_greater_than(field_value, expected_value)
            elif operator == '<=':
                return self._compare_less_equal(field_value, expected_value)
            elif operator == '>=':
                return self._compare_greater_equal(field_value, expected_value)
            elif operator == 'in':
                return self._compare_in(field_value, expected_value)
            elif operator == 'not in':
                return not self._compare_in(field_value, expected_value)
            elif operator == 'like':
                return self._compare_like(field_value, expected_value)
            elif operator == 'ilike':
                return self._compare_ilike(field_value, expected_value)
            else:
                self.logger.warning(f"Unsupported operator '{operator}', defaulting to False")
                return False
                
        except Exception as e:
            self.logger.warning(f"Error evaluating condition {condition}: {e}")
            return False  # Fail safe - show field on evaluation error
    
    def _get_field_value(self, field_path: str, context: Dict[str, Any], user_context: Dict[str, Any] = None) -> Any:
        """
        Get field value from context, supporting dot notation for related fields and user context.
        
        Args:
            field_path: Field path like 'field', 'related.sub_field', or 'user.role.name'
            context: Context dictionary
            user_context: User information dictionary
            
        Returns:
            Field value or None if not found
        """
        try:
            parts = field_path.split('.')
            
            # Check if this is a user context reference
            if parts[0] == 'user' and user_context:
                value = user_context
                for part in parts[1:]:  # Skip 'user' prefix
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = getattr(value, part, None)
                    if value is None:
                        break
                return value
            
            # Regular field context lookup
            value = context
            
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return None
                
                if value is None:
                    return None
            
            return value
            
        except Exception as e:
            self.logger.warning(f"Error getting field value for '{field_path}': {e}")
            return None
    
    def _compare_equal(self, field_value: Any, expected_value: Any) -> bool:
        """
        Compare two values for equality, handling different types and enterprise patterns.
        
        Enterprise patterns supported:
        - ('field', '=', False) - Check if field is empty/null
        - ('field', '!=', False) - Check if field is not empty/null
        - ('many2one_field', '=', False) - Check if many2one field is empty
        - ('char_field', '=', False) - Check if char field is empty
        """
        
        # Handle enterprise empty/null checking patterns
        if expected_value is False:
            return self._is_empty_value(field_value)
        
        # Handle None values
        if field_value is None and expected_value is None:
            return True
        if field_value is None or expected_value is None:
            return False
        
        # Handle many2one fields (dict with id)
        if isinstance(field_value, dict) and 'id' in field_value:
            field_value = field_value['id']
        
        # Handle boolean comparisons
        if isinstance(expected_value, bool):
            return bool(field_value) == expected_value
        
        # Handle string comparisons (case-sensitive)
        if isinstance(expected_value, str):
            return str(field_value) == expected_value
        
        # Handle numeric comparisons
        try:
            return field_value == expected_value
        except Exception:
            return str(field_value) == str(expected_value)
    
    def _is_empty_value(self, value: Any) -> bool:
        """
        Check if a value is considered empty for enterprise domain logic.
        
        Empty values:
        - None
        - Empty string ('')
        - Empty list ([])
        - Empty dict ({})
        - Zero (0) for many2one fields
        - False (boolean)
        - Many2one dict with id=None or id=0
        """
        # None is always empty
        if value is None:
            return True
        
        # Boolean False is empty
        if value is False:
            return True
        
        # Empty string
        if isinstance(value, str) and value.strip() == '':
            return True
        
        # Empty collections
        if isinstance(value, (list, dict, tuple)) and len(value) == 0:
            return True
        
        # Many2one field represented as dict
        if isinstance(value, dict):
            if 'id' in value:
                # Many2one with null or zero id is empty
                return value['id'] is None or value['id'] == 0 or value['id'] == ''
            # Empty dict is empty
            return len(value) == 0
        
        # Zero for many2one IDs (common pattern)
        if isinstance(value, (int, float)) and value == 0:
            return True
        
        # Everything else is not empty
        return False
    
    def _compare_less_than(self, field_value: Any, expected_value: Any) -> bool:
        """Compare field_value < expected_value"""
        if field_value is None or expected_value is None:
            return False
        
        try:
            return field_value < expected_value
        except TypeError:
            # Try string comparison as fallback
            return str(field_value) < str(expected_value)
    
    def _compare_greater_than(self, field_value: Any, expected_value: Any) -> bool:
        """Compare field_value > expected_value"""
        if field_value is None or expected_value is None:
            return False
        
        try:
            return field_value > expected_value
        except TypeError:
            # Try string comparison as fallback
            return str(field_value) > str(expected_value)
    
    def _compare_less_equal(self, field_value: Any, expected_value: Any) -> bool:
        """Compare field_value <= expected_value"""
        return self._compare_less_than(field_value, expected_value) or self._compare_equal(field_value, expected_value)
    
    def _compare_greater_equal(self, field_value: Any, expected_value: Any) -> bool:
        """Compare field_value >= expected_value"""
        return self._compare_greater_than(field_value, expected_value) or self._compare_equal(field_value, expected_value)
    
    def _compare_in(self, field_value: Any, expected_values: Any) -> bool:
        """Check if field_value is in expected_values list"""
        if not isinstance(expected_values, (list, tuple, set)):
            return self._compare_equal(field_value, expected_values)
        
        # Handle many2one fields
        if isinstance(field_value, dict) and 'id' in field_value:
            field_value = field_value['id']
        
        return field_value in expected_values
    
    def _compare_like(self, field_value: Any, pattern: Any) -> bool:
        """Case-sensitive pattern matching (SQL LIKE)"""
        if field_value is None or pattern is None:
            return False
        
        field_str = str(field_value)
        pattern_str = str(pattern)
        
        # Convert SQL LIKE pattern to regex
        regex_pattern = pattern_str.replace('%', '.*').replace('_', '.')
        return bool(re.search(regex_pattern, field_str))
    
    def _compare_ilike(self, field_value: Any, pattern: Any) -> bool:
        """Case-insensitive pattern matching (SQL ILIKE)"""
        if field_value is None or pattern is None:
            return False
        
        field_str = str(field_value).lower()
        pattern_str = str(pattern).lower()
        
        # Convert SQL LIKE pattern to regex
        regex_pattern = pattern_str.replace('%', '.*').replace('_', '.')
        return bool(re.search(regex_pattern, field_str))
    
    def validate_expression(self, expression: str, available_fields: List[str] = None) -> ValidationResult:
        """
        Validate a domain expression for syntax and field references.
        
        Args:
            expression: Domain expression to validate
            available_fields: List of available field names for validation
            
        Returns:
            ValidationResult with validation status and messages
        """
        errors = []
        warnings = []
        
        try:
            if not expression or not expression.strip():
                return ValidationResult(is_valid=True, errors=errors, warnings=warnings)
            
            # Parse the expression
            domain_ast = self.parse_expression(expression)
            
            # Validate field references and operators within groups
            for group in domain_ast.groups:
                for condition in group.conditions:
                    # Validate field references if available_fields provided
                    if available_fields is not None:
                        field_parts = condition.field.split('.')
                        base_field = field_parts[0]
                        
                        if base_field not in available_fields:
                            warnings.append(f"Field '{base_field}' not found in available fields")
                    
                    # Validate operator usage
                    if condition.operator in ['in', 'not in']:
                        if not isinstance(condition.value, (list, tuple)):
                            warnings.append(f"Operator '{condition.operator}' expects a list value, got {type(condition.value).__name__}")
                    
                    if condition.operator in ['like', 'ilike']:
                        if not isinstance(condition.value, str):
                            warnings.append(f"Operator '{condition.operator}' expects a string value, got {type(condition.value).__name__}")
            
            return ValidationResult(is_valid=True, errors=errors, warnings=warnings)
            
        except DomainParseError as e:
            errors.append(str(e))
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    
    def safe_evaluate(self, expression: str, context: Dict[str, Any], default: bool = True, user_context: Dict[str, Any] = None) -> bool:
        """
        Safely evaluate a domain expression with error handling and security validation.
        
        Args:
            expression: Domain expression to evaluate
            context: Field values context
            default: Default value to return on error
            user_context: User information context from JWT claims (secure)
            
        Returns:
            Boolean result or default value on error
        """
        try:
            # Validate user_context security if provided
            if user_context and not self.validate_secure_user_context(user_context):
                self.logger.warning("Domain engine: Insecure user_context in safe_evaluate, using default")
                return default
            
            return self.evaluate(expression, context, user_context)
        except Exception as e:
            self.logger.warning(f"Domain evaluation failed, using default ({default}): {e}")
            return default


# Global domain engine instance
domain_engine = DomainEngine()


def create_secure_user_context_from_jwt(jwt_claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create secure user context from validated JWT claims for domain engine evaluation.
    
    This function ensures that user context is derived from server-validated JWT tokens
    instead of client-side localStorage, preventing security vulnerabilities.
    
    Args:
        jwt_claims: Validated JWT token claims
        
    Returns:
        Secure user context dictionary for domain engine
    """
    try:
        return {
            'id': jwt_claims.get('user_id'),
            'email': jwt_claims.get('email'),
            'full_name': jwt_claims.get('full_name'),
            'role': {
                'name': jwt_claims.get('role'),
                'permissions': jwt_claims.get('permissions', [])
            },
            'preferences': jwt_claims.get('preferences', {}),

            'is_active': jwt_claims.get('is_active', True),
            '_source': 'jwt'  # Security marker to indicate JWT source
        }
    except Exception as e:
        logger.error(f"Error creating secure user context from JWT: {e}")
        return {}