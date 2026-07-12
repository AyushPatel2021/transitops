/**
 * Frontend Domain Expression Engine
 * 
 * This module provides parsing and evaluation of domain expressions for conditional
 * field visibility and readonly states. Supports both simple and complex logical operations.
 * 
 * Example domain expressions:
 * Simple (implicit AND):
 * - "[('status', '=', 'draft')]"
 * - "[('amount', '>', 100), ('state', 'in', ['pending', 'approved'])]"
 * 
 * Complex with explicit logical operators:
 * - "[[('status', '=', 'scrapped'), ('user.role.name', '!=', 'admin')], '|', ('is_active', '!=', false)]"
 *   Means: (status = 'scrapped' AND user.role.name != 'admin') OR (is_active != false)
 */

export interface DomainCondition {
  field: string;
  operator: string;
  value: any;
}

export interface DomainGroup {
  conditions: DomainCondition[];
}

export interface DomainAST {
  groups: DomainGroup[];
  operators: string[]; // Logical operators between groups ('&' for AND, '|' for OR)
}

export class DomainParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DomainParseError';
  }
}

export class DomainEvaluationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DomainEvaluationError';
  }
}

import { useAuth } from './useAuth';

export class DomainEngine {
  private static readonly SUPPORTED_OPERATORS = new Set([
    '=', '!=', '<', '>', '<=', '>=', 
    'in', 'not in', 'like', 'ilike'
  ]);
  
  private static readonly LOGICAL_OPERATORS = new Set(['&', '|']);
  
  /**
   * Parse a domain expression string into a DomainAST.
   * Supports both simple and complex formats.
   */
  parseExpression(expression: string, context: Record<string, any> = {}): DomainAST {
    if (!expression || !expression.trim()) {
      return { groups: [], operators: [] };
    }
    
    try {
      // Remove whitespace and validate basic structure
      const expr = expression.trim();
      if (!expr.startsWith('[') || !expr.endsWith(']')) {
        throw new DomainParseError(`Domain expression must be wrapped in brackets: ${expression}`);
      }
      
      // Parse the expression safely with context
      const parsed = this.safeEval(expr, context);
      
      if (!Array.isArray(parsed)) {
        throw new DomainParseError(`Domain expression must be a list: ${expression}`);
      }
      
      // Check if this is a complex format (contains nested arrays and operators)
      const hasNestedArrays = parsed.some(item => Array.isArray(item));
      const hasOperators = parsed.some(item => typeof item === 'string' && DomainEngine.LOGICAL_OPERATORS.has(item));
      
      if (hasNestedArrays || hasOperators) {
        return this.parseComplexExpression(parsed, expression);
      } else {
        return this.parseSimpleExpression(parsed, expression);
      }
      
    } catch (error) {
      if (error instanceof DomainParseError) {
        throw error;
      }
      throw new DomainParseError(`Failed to parse domain expression: ${expression}. Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Parse simple format: [('field', '=', 'value'), ('field2', '>', 100)]
   */
  private parseSimpleExpression(parsed: any[], originalExpr: string): DomainAST {
    const conditions: DomainCondition[] = [];
    
    for (const item of parsed) {
      if (!Array.isArray(item) || item.length !== 3) {
        throw new DomainParseError(`Each condition must be a 3-tuple (field, operator, value): ${JSON.stringify(item)}`);
      }
      
      const [field, operator, value] = item;
      
      if (typeof field !== 'string') {
        throw new DomainParseError(`Field name must be a string: ${field}`);
      }
      
      if (typeof operator !== 'string' || !DomainEngine.SUPPORTED_OPERATORS.has(operator)) {
        throw new DomainParseError(`Unsupported operator '${operator}'. Supported: ${Array.from(DomainEngine.SUPPORTED_OPERATORS).join(', ')}`);
      }
      
      conditions.push({ field, operator, value });
    }
    
    // Simple format has one group with implicit AND
    const group: DomainGroup = { conditions };
    return { groups: [group], operators: [] };
  }
  
  /**
   * Parse complex format: [[('field1', '=', 'value1')], '|', [('field2', '>', 100)]]
   */
  private parseComplexExpression(parsed: any[], originalExpr: string): DomainAST {
    const groups: DomainGroup[] = [];
    const operators: string[] = [];
    
    let i = 0;
    while (i < parsed.length) {
      const item = parsed[i];
      
      if (typeof item === 'string' && DomainEngine.LOGICAL_OPERATORS.has(item)) {
        operators.push(item);
        i++;
      } else if (Array.isArray(item)) {
        // Check if this is a group of conditions or a single condition
        if (item.length === 3 && typeof item[0] === 'string') {
          // Single condition not wrapped in a list - treat as a single-condition group
          const [field, operator, value] = item;
          
          if (typeof operator !== 'string' || !DomainEngine.SUPPORTED_OPERATORS.has(operator)) {
            throw new DomainParseError(`Unsupported operator '${operator}'. Supported: ${Array.from(DomainEngine.SUPPORTED_OPERATORS).join(', ')}`);
          }
          
          const condition: DomainCondition = { field, operator, value };
          groups.push({ conditions: [condition] });
        } else {
          // Parse this group of conditions
          const conditions: DomainCondition[] = [];
          for (const conditionItem of item) {
            if (!Array.isArray(conditionItem) || conditionItem.length !== 3) {
              throw new DomainParseError(`Each condition must be a 3-tuple (field, operator, value): ${JSON.stringify(conditionItem)}`);
            }
            
            const [field, operator, value] = conditionItem;
            
            if (typeof field !== 'string') {
              throw new DomainParseError(`Field name must be a string: ${field}`);
            }
            
            if (typeof operator !== 'string' || !DomainEngine.SUPPORTED_OPERATORS.has(operator)) {
              throw new DomainParseError(`Unsupported operator '${operator}'. Supported: ${Array.from(DomainEngine.SUPPORTED_OPERATORS).join(', ')}`);
            }
            
            conditions.push({ field, operator, value });
          }
          
          groups.push({ conditions });
        }
        i++;
      } else {
        throw new DomainParseError(`Invalid item in complex expression: ${JSON.stringify(item)}`);
      }
    }
    
    // Validate that we have the right number of operators
    if (operators.length !== groups.length - 1) {
      throw new DomainParseError(`Number of operators (${operators.length}) must be one less than number of groups (${groups.length})`);
    }
    
    return { groups, operators };
  }

  /**
   * Evaluate a domain expression against a context (form data).
   */
  evaluate(expression: string, context: Record<string, any>): boolean {
    if (!expression || !expression.trim()) {
      return true;
    }

    try {
      // Add user context
      const { user } = useAuth();
      const fullContext = {
        ...context,
        user: user.value || {}
      };

      // 1. Initial string parsing to get the list
      const parsed = this.safeEval(expression.trim(), fullContext);
      if (!Array.isArray(parsed)) return true;

      // 2. Recursive evaluation
      const tokens = [...parsed];
      const results: boolean[] = [];

      const evaluateRecursive = (tokens: any[]): boolean => {
        if (tokens.length === 0) return true;

        const token = tokens.shift();

        if (token === '|') {
          const left = evaluateRecursive(tokens);
          const right = evaluateRecursive(tokens);
          return left || right;
        } else if (token === '&') {
          const left = evaluateRecursive(tokens);
          const right = evaluateRecursive(tokens);
          return left && right;
        } else if (token === '!') {
          return !evaluateRecursive(tokens);
        } else if (Array.isArray(token) && token.length === 3) {
          return this.evaluateCondition({
            field: token[0] as string,
            operator: token[1] as string,
            value: token[2]
          }, fullContext);
        } else if (Array.isArray(token)) {
          // Nested list - in Odoo this is usually an implicit AND if it's the top level
          // but we'll try to evaluate it recursively.
          // Note: Odoo doesn't typically nest without operators, but we'll be safe.
          const nestedTokens = [...token];
          const nestedFilters: boolean[] = [];
          while (nestedTokens.length > 0) {
            nestedFilters.push(evaluateRecursive(nestedTokens));
          }
          return nestedFilters.every(r => r);
        }
        
        return true;
      };

      // Process tokens. Top level is implicit AND if there are multiple results
      while (tokens.length > 0) {
        results.push(evaluateRecursive(tokens));
      }

      return results.every(r => r);

    } catch (error) {
      console.error('Domain evaluation error:', error);
      return true; // Default to true (visible/active) on error
    }
  }

  /**
   * Resolve a domain expression to a static list of conditions.
   * Useful for Many2one filtering where you need the evaluated list, not a boolean result.
   */
  resolveDomain(expression: string, context: Record<string, any>): any[] {
    try {
      if (!expression || !expression.trim()) {
        return [];
      }

      // Add user context
      const { user } = useAuth();
      const fullContext = {
        ...context,
        user: user.value || {}
      };

      return this.safeEval(expression, fullContext);
    } catch (error) {
      return [];
    }
  }

  /**
   * Evaluate a group of conditions (implicit AND between conditions).
   */
  private evaluateGroup(group: DomainGroup, context: Record<string, any>): boolean {
    if (!group.conditions.length) {
      return true;
    }
    
    const results = group.conditions.map(condition => 
      this.evaluateCondition(condition, context)
    );
    
    // All conditions in a group must be true (implicit AND)
    return results.every(result => result);
  }
  
  /**
   * Evaluate a single domain condition.
   */
  private evaluateCondition(condition: DomainCondition, context: Record<string, any>): boolean {
    const fieldValue = this.getFieldValue(condition.field, context);
    const expectedValue = condition.value;
    const operator = condition.operator;
    
    try {
      switch (operator) {
        case '=':
          return this.compareEqual(fieldValue, expectedValue);
        case '!=':
          return !this.compareEqual(fieldValue, expectedValue);
        case '<':
          return this.compareLessThan(fieldValue, expectedValue);
        case '>':
          return this.compareGreaterThan(fieldValue, expectedValue);
        case '<=':
          return this.compareLessEqual(fieldValue, expectedValue);
        case '>=':
          return this.compareGreaterEqual(fieldValue, expectedValue);
        case 'in':
          return this.compareIn(fieldValue, expectedValue);
        case 'not in':
          return !this.compareIn(fieldValue, expectedValue);
        case 'like':
          return this.compareLike(fieldValue, expectedValue);
        case 'ilike':
          return this.compareILike(fieldValue, expectedValue);
        default:
          return false;
      }
    } catch (error) {
      return false; // Fail safe - show field on evaluation error
    }
  }
  
  /**
   * Get field value from context, supporting dot notation for related fields.
   */
  private getFieldValue(fieldPath: string, context: Record<string, any>): any {
    try {
      const parts = fieldPath.split('.');
      let value: any = context;
      
      for (const part of parts) {
        if (value && typeof value === 'object' && part in value) {
          value = value[part];
        } else {
          return null;
        }
        
        if (value === null || value === undefined) {
          return null;
        }
      }
      
      return value;
    } catch (error) {
      return null;
    }
  }
  
  /**
   * Compare two values for equality, handling different types and enterprise patterns.
   */
  private compareEqual(fieldValue: any, expectedValue: any): boolean {
    // Handle enterprise empty/null checking patterns
    if (expectedValue === false) {
      return this.isEmptyValue(fieldValue);
    }
    
    // Handle null values
    if (fieldValue === null && expectedValue === null) {
      return true;
    }
    if (fieldValue === null || expectedValue === null) {
      return false;
    }
    
    // Handle many2one fields (object with id)
    if (typeof fieldValue === 'object' && fieldValue !== null && 'id' in fieldValue) {
      fieldValue = fieldValue.id;
    }
    
    // Handle boolean comparisons
    if (typeof expectedValue === 'boolean') {
      return Boolean(fieldValue) === expectedValue;
    }
    
    // Handle string comparisons
    if (typeof expectedValue === 'string') {
      return String(fieldValue) === expectedValue;
    }
    
    // Handle array comparisons (specifically for empty arrays in domains)
    if (Array.isArray(fieldValue) && Array.isArray(expectedValue)) {
      if (fieldValue.length === 0 && expectedValue.length === 0) return true;
    }
    
    // Handle numeric and other comparisons
    return fieldValue === expectedValue;
  }
  
  /**
   * Check if a value is considered empty for enterprise domain logic.
   */
  private isEmptyValue(value: any): boolean {
    // null/undefined is always empty
    if (value === null || value === undefined) {
      return true;
    }
    
    // Boolean false is empty
    if (value === false) {
      return true;
    }
    
    // Empty string
    if (typeof value === 'string' && value.trim() === '') {
      return true;
    }
    
    // Empty arrays
    if (Array.isArray(value) && value.length === 0) {
      return true;
    }
    
    // Empty objects
    if (typeof value === 'object' && value !== null) {
      if ('id' in value) {
        // Many2one with null or zero id is empty
        return value.id === null || value.id === undefined || value.id === 0 || value.id === '';
      }
      // Empty object is empty
      return Object.keys(value).length === 0;
    }
    
    // Zero for many2one IDs (common pattern)
    if (typeof value === 'number' && value === 0) {
      return true;
    }
    
    // Everything else is not empty
    return false;
  }
  
  /**
   * Compare field_value < expected_value.
   */
  private compareLessThan(fieldValue: any, expectedValue: any): boolean {
    if (fieldValue === null || expectedValue === null) {
      return false;
    }
    
    try {
      return fieldValue < expectedValue;
    } catch {
      // Try string comparison as fallback
      return String(fieldValue) < String(expectedValue);
    }
  }
  
  /**
   * Compare field_value > expected_value.
   */
  private compareGreaterThan(fieldValue: any, expectedValue: any): boolean {
    if (fieldValue === null || expectedValue === null) {
      return false;
    }
    
    try {
      return fieldValue > expectedValue;
    } catch {
      // Try string comparison as fallback
      return String(fieldValue) > String(expectedValue);
    }
  }
  
  /**
   * Compare field_value <= expected_value.
   */
  private compareLessEqual(fieldValue: any, expectedValue: any): boolean {
    return this.compareLessThan(fieldValue, expectedValue) || this.compareEqual(fieldValue, expectedValue);
  }
  
  /**
   * Compare field_value >= expected_value.
   */
  private compareGreaterEqual(fieldValue: any, expectedValue: any): boolean {
    return this.compareGreaterThan(fieldValue, expectedValue) || this.compareEqual(fieldValue, expectedValue);
  }
  
  /**
   * Check if field_value is in expected_values list.
   */
  private compareIn(fieldValue: any, expectedValues: any): boolean {
    if (!Array.isArray(expectedValues)) {
      return this.compareEqual(fieldValue, expectedValues);
    }
    
    // Handle many2one fields
    if (typeof fieldValue === 'object' && fieldValue !== null && 'id' in fieldValue) {
      fieldValue = fieldValue.id;
    }
    
    return expectedValues.includes(fieldValue);
  }
  
  /**
   * Case-sensitive pattern matching (SQL LIKE).
   */
  private compareLike(fieldValue: any, pattern: any): boolean {
    if (fieldValue === null || pattern === null) {
      return false;
    }
    
    const fieldStr = String(fieldValue);
    const patternStr = String(pattern);
    
    // Convert SQL LIKE pattern to regex
    const regexPattern = patternStr.replace(/%/g, '.*').replace(/_/g, '.');
    const regex = new RegExp(regexPattern);
    
    return regex.test(fieldStr);
  }
  
  /**
   * Case-insensitive pattern matching (SQL ILIKE).
   */
  private compareILike(fieldValue: any, pattern: any): boolean {
    if (fieldValue === null || pattern === null) {
      return false;
    }
    
    const fieldStr = String(fieldValue).toLowerCase();
    const patternStr = String(pattern).toLowerCase();
    
    // Convert SQL LIKE pattern to regex
    const regexPattern = patternStr.replace(/%/g, '.*').replace(/_/g, '.');
    const regex = new RegExp(regexPattern);
    
    return regex.test(fieldStr);
  }

  /**
   * Safe evaluation of JavaScript expressions (limited to JSON-like structures and variable resolution).
   */
  private safeEval(expression: string, context: Record<string, any> = {}): any {
    // Basic python-to-js conversion
    let jsExpression = expression
      .replace(/'/g, '"')
      .replace(/\(/g, '[')
      .replace(/\)/g, ']')
      .replace(/\bTrue\b/g, 'true')
      .replace(/\bFalse\b/g, 'false')
      .replace(/\bNone\b/g, 'null');
      
    try {
      // First try JSON.parse (fastest, safest)
      return JSON.parse(jsExpression);
    } catch {
      // Fallback: evaluate with context using Function
      try {
        if (this.isSafeExpression(expression)) {
          const keys = Object.keys(context);
          const values = Object.values(context);
          // Create function with context keys as arguments
          return new Function(...keys, `"use strict"; return (${jsExpression})`)(...values);
        } else {
          throw new Error('Unsafe expression');
        }
      } catch (error) {
        throw new DomainParseError(`Cannot parse expression: ${expression}`);
      }
    }
  }
  
  /**
   * Check if an expression is safe to evaluate.
   */
  private isSafeExpression(expression: string): boolean {
    // Allow expressions that look like domain arrays (both Python and JavaScript style)
    // Updated patterns to allow boolean values (True, False, true, false) and None/null
    const pythonPattern = /^\s*\[\s*(\(\s*['"][^'"]*['"]\s*,\s*['"][^'"]*['"]\s*,\s*[^)]*\)\s*,?\s*)*\]\s*$/;
    const jsPattern = /^\s*\[\s*(\[\s*["'][^'"]*["']\s*,\s*["'][^'"]*["']\s*,\s*[^\]]*\]\s*,?\s*)*\]\s*$/;
    
    // More permissive pattern that allows complex nested structures with booleans
    const complexPattern = /^\s*\[.*\]\s*$/;
    
    // Check for dangerous patterns
    const dangerousPatterns = [
      /function\s*\(/i,
      /eval\s*\(/i,
      /new\s+/i,
      /import\s+/i,
      /require\s*\(/i,
      /process\./i,
      /global\./i,
      /window\./i,
      /document\./i
    ];
    
    // Reject if contains dangerous patterns
    if (dangerousPatterns.some(pattern => pattern.test(expression))) {
      return false;
    }
    
    return pythonPattern.test(expression) || jsPattern.test(expression) || complexPattern.test(expression);
  }

  /**
   * Safely evaluate a domain expression with error handling.
   */
  safeEvaluate(expression: string, context: Record<string, any>, defaultValue: boolean = true): boolean {
    try {
      return this.evaluate(expression, context);
    } catch (error) {
      return defaultValue;
    }
  }

  /**
   * Alias for safeEvaluate for backward compatibility
   */
  evaluateWithDefault(expression: string, context: Record<string, any>, defaultValue: boolean = true): boolean {
    return this.safeEvaluate(expression, context, defaultValue);
  }
}