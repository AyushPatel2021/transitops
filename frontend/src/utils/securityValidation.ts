/**
 * Security Validation Utilities
 * 
 * This module provides security validation functions to ensure localStorage
 * only contains JWT tokens and no sensitive user data, preventing client-side
 * data manipulation attacks.
 * 
 * Requirements: 6.2, 6.5, 8.1
 */

export interface SecurityValidationResult {
  isSecure: boolean;
  violations: string[];
  recommendations: string[];
}

export interface LocalStorageAuditResult {
  totalKeys: number;
  allowedKeys: string[];
  violatingKeys: string[];
  sensitiveDataFound: boolean;
}

// Allowed localStorage keys (only JWT token should be present)
const ALLOWED_LOCALSTORAGE_KEYS = [
  'token',
  'sidebar_collapsed',
  'sidebar_expanded_items',
  'google_oauth_state' // Temporary OAuth state
];

// Sensitive data patterns that should never be in localStorage
const SENSITIVE_DATA_PATTERNS = [
  /user/i,
  /profile/i,
  /role/i,
  /permission/i,
  /auth(?!_state)/i, // auth but not auth_state
  /password/i,
  /email/i,

  /preference/i
];

/**
 * Audit localStorage for security violations
 */
export function auditLocalStorage(): LocalStorageAuditResult {
  const keys: string[] = [];
  
  // Get all keys from localStorage
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) {
        keys.push(key);
      }
    }
  } catch (error) {
    // Fallback: try Object.keys if available
    try {
      const storageKeys = Object.keys(localStorage);
      keys.push(...storageKeys.filter(key => 
        !['getItem', 'setItem', 'removeItem', 'clear', 'key', 'length'].includes(key)
      ));
    } catch (fallbackError) {
      
    }
  }
  
  const allowedKeys: string[] = [];
  const violatingKeys: string[] = [];
  
  keys.forEach(key => {
    if (ALLOWED_LOCALSTORAGE_KEYS.includes(key)) {
      allowedKeys.push(key);
    } else {
      violatingKeys.push(key);
    }
  });
  
  // Check for sensitive data patterns
  const sensitiveDataFound = violatingKeys.some(key => 
    SENSITIVE_DATA_PATTERNS.some(pattern => pattern.test(key))
  );
  
  return {
    totalKeys: keys.length,
    allowedKeys,
    violatingKeys,
    sensitiveDataFound
  };
}

/**
 * Validate localStorage security compliance
 */
export function validateLocalStorageSecurity(): SecurityValidationResult {
  const audit = auditLocalStorage();
  const violations: string[] = [];
  const recommendations: string[] = [];
  
  // Check for violating keys
  if (audit.violatingKeys.length > 0) {
    violations.push(`Unauthorized keys found in localStorage: ${audit.violatingKeys.join(', ')}`);
    recommendations.push('Remove unauthorized keys from localStorage');
  }
  
  // Check for sensitive data patterns
  if (audit.sensitiveDataFound) {
    violations.push('Sensitive user data detected in localStorage');
    recommendations.push('Move sensitive data to memory-based storage (UserStore)');
  }
  
  // Note: JWT tokens are now managed in memory by UserStore
  // localStorage should only contain UI preferences and non-sensitive data
  // This is the expected secure behavior
  
  return {
    isSecure: violations.length === 0,
    violations,
    recommendations
  };
}

/**
 * Clean up unauthorized localStorage entries
 */
export function cleanupLocalStorage(): { removed: string[], kept: string[] } {
  const audit = auditLocalStorage();
  const removed: string[] = [];
  const kept: string[] = [];
  
  // Remove violating keys
  audit.violatingKeys.forEach(key => {
    try {
      localStorage.removeItem(key);
      removed.push(key);
      
    } catch (error) {
      
    }
  });
  
  // Keep allowed keys
  audit.allowedKeys.forEach(key => {
    kept.push(key);
  });
  
  return { removed, kept };
}

/**
 * Migrate from old localStorage-based user system
 */
export function migrateFromLegacyLocalStorage(): { migrated: boolean, data: any } {
  const legacyUserData = localStorage.getItem('user');
  
  if (!legacyUserData) {
    return { migrated: false, data: null };
  }
  
  try {
    const userData = JSON.parse(legacyUserData);
    
    // Log migration for audit purposes
    
    
    
    // Remove legacy user data from localStorage
    localStorage.removeItem('user');
    
    // Additional cleanup of common legacy keys
    const legacyKeys = ['profile', 'auth_user', 'current_user', 'user_preferences'];
    legacyKeys.forEach(key => {
      if (localStorage.getItem(key)) {
        localStorage.removeItem(key);
        
      }
    });
    
    return { migrated: true, data: userData };
  } catch (error) {
    
    // Remove corrupted data
    localStorage.removeItem('user');
    return { migrated: false, data: null };
  }
}

/**
 * Detect potential JWT tampering attempts
 */
export function detectJWTTampering(token: string): { tampered: boolean, issues: string[] } {
  const issues: string[] = [];
  
  if (!token) {
    return { tampered: false, issues: [] };
  }
  
  try {
    // Check JWT structure (should have 3 parts separated by dots)
    const parts = token.split('.');
    if (parts.length !== 3) {
      issues.push('Invalid JWT structure - should have 3 parts');
      return { tampered: true, issues };
    }
    
    // Check if parts are valid base64
    parts.forEach((part, index) => {
      try {
        atob(part.replace(/-/g, '+').replace(/_/g, '/'));
      } catch (error) {
        issues.push(`Invalid base64 encoding in JWT part ${index + 1}`);
      }
    });
    
    // Decode header and payload (without signature verification)
    try {
      const header = JSON.parse(atob(parts[0].replace(/-/g, '+').replace(/_/g, '/')));
      const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
      
      // Check for required header fields
      if (!header.alg || !header.typ) {
        issues.push('Missing required JWT header fields');
      }
      
      // Check for required payload fields
      const requiredFields = ['sub', 'user_id', 'exp', 'iat'];
      requiredFields.forEach(field => {
        if (!(field in payload)) {
          issues.push(`Missing required JWT claim: ${field}`);
        }
      });
      
      // Check expiration
      if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
        issues.push('JWT token is expired');
      }
      
      // Check issued at time (should not be in the future)
      if (payload.iat && payload.iat > Math.floor(Date.now() / 1000) + 60) {
        issues.push('JWT issued at time is in the future');
      }
      
    } catch (error) {
      issues.push('Failed to decode JWT payload');
    }
    
  } catch (error) {
    issues.push('General JWT validation error');
  }
  
  return {
    tampered: issues.length > 0,
    issues
  };
}

/**
 * Validate user permissions against JWT claims
 */
export function validatePermissions(
  requestedPermissions: string[],
  jwtClaims: any
): { authorized: boolean, violations: string[] } {
  const violations: string[] = [];
  
  if (!jwtClaims || !jwtClaims.permissions) {
    violations.push('No permissions found in JWT claims');
    return { authorized: false, violations };
  }
  
  const userPermissions = jwtClaims.permissions || [];
  
  requestedPermissions.forEach(permission => {
    if (!userPermissions.includes(permission)) {
      violations.push(`Missing permission: ${permission}`);
    }
  });
  
  return {
    authorized: violations.length === 0,
    violations
  };
}

/**
 * Security monitoring - log security events
 */
export function logSecurityEvent(
  eventType: 'localStorage_violation' | 'jwt_tampering' | 'permission_violation' | 'migration_completed',
  details: any
): void {
  const timestamp = new Date().toISOString();
  const event = {
    timestamp,
    type: eventType,
    details,
    userAgent: navigator.userAgent,
    url: window.location.href
  };
  
  // Log to console for development
  
  
  // In production, this could send to a security monitoring service
  // Example: sendToSecurityService(event);
}

/**
 * Comprehensive security validation
 */
export function performSecurityAudit(): {
  localStorage: SecurityValidationResult;
  jwt: { tampered: boolean; issues: string[] } | null;
  overall: { secure: boolean; criticalIssues: string[] };
} {
  const localStorageResult = validateLocalStorageSecurity();
  
  // Note: JWT tokens are now managed in memory by UserStore, not localStorage
  // This is the expected secure behavior
  const jwtResult = null;
  
  // Determine overall security status
  const criticalIssues: string[] = [];
  
  if (!localStorageResult.isSecure) {
    criticalIssues.push(...localStorageResult.violations);
  }
  
  const overallSecure = criticalIssues.length === 0;
  
  // Log security audit results only if there are actual violations
  if (!overallSecure) {
    logSecurityEvent('localStorage_violation', {
      localStorage: localStorageResult,
      jwt: jwtResult,
      criticalIssues
    });
  }
  
  return {
    localStorage: localStorageResult,
    jwt: jwtResult,
    overall: {
      secure: overallSecure,
      criticalIssues
    }
  };
}