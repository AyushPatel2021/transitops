/**
 * Security Service
 * 
 * Provides comprehensive security monitoring and validation for the application.
 * Integrates with UserStore to ensure secure user data management and prevent
 * client-side data manipulation attacks.
 * 
 * Requirements: 6.2, 6.5, 8.1, 8.4, 8.5
 */

import { 
  performSecurityAudit, 
  cleanupLocalStorage, 
  migrateFromLegacyLocalStorage,
  logSecurityEvent,
  validatePermissions,
  detectJWTTampering
} from '../utils/securityValidation';

export interface SecurityConfig {
  enableAutoCleanup: boolean;
  enablePeriodicAudit: boolean;
  auditIntervalMs: number;
  enableMigration: boolean;
  logSecurityEvents: boolean;
}

export interface SecurityStatus {
  isSecure: boolean;
  lastAudit: Date | null;
  issues: string[];
  migratedData: boolean;
}

class SecurityService {
  private config: SecurityConfig;
  private status: SecurityStatus;
  private auditTimer: number | null = null;
  private initialized = false;

  constructor(config: Partial<SecurityConfig> = {}) {
    this.config = {
      enableAutoCleanup: true,
      enablePeriodicAudit: true,
      auditIntervalMs: 60000, // 1 minute
      enableMigration: true,
      logSecurityEvents: true,
      ...config
    };

    this.status = {
      isSecure: false,
      lastAudit: null,
      issues: [],
      migratedData: false
    };
  }

  /**
   * Initialize security service
   */
  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    

    try {
      // Perform initial migration if enabled
      if (this.config.enableMigration) {
        await this.performMigration();
      }

      // Perform initial security audit
      await this.performAudit();

      // Setup periodic auditing if enabled
      if (this.config.enablePeriodicAudit) {
        this.startPeriodicAudit();
      }

      this.initialized = true;
      

    } catch (error) {
      
      throw error;
    }
  }

  /**
   * Perform migration from legacy localStorage system
   */
  private async performMigration(): Promise<any> {
    

    const migrationResult = migrateFromLegacyLocalStorage();
    
    if (migrationResult.migrated) {
      this.status.migratedData = true;
      
      if (this.config.logSecurityEvents) {
        logSecurityEvent('migration_completed', {
          migratedData: migrationResult.data,
          timestamp: new Date().toISOString()
        });
      }

      
      return migrationResult.data;
    } else {
      
      return null;
    }
  }

  /**
   * Perform comprehensive security audit
   */
  async performAudit(): Promise<void> {
    

    try {
      const auditResult = performSecurityAudit();
      
      this.status.isSecure = auditResult.overall.secure;
      this.status.lastAudit = new Date();
      this.status.issues = auditResult.overall.criticalIssues;

      if (!auditResult.overall.secure) {
        

        // Auto-cleanup if enabled
        if (this.config.enableAutoCleanup) {
          await this.performCleanup();
        }

        // Log security violations
        if (this.config.logSecurityEvents) {
          logSecurityEvent('localStorage_violation', auditResult);
        }
      } else {
        
      }

    } catch (error) {
      
      this.status.issues.push('Security audit failed');
    }
  }

  /**
   * Perform localStorage cleanup
   */
  async performCleanup(): Promise<void> {
    

    try {
      const cleanupResult = cleanupLocalStorage();
      
      if (cleanupResult.removed.length > 0) {
        
        
        if (this.config.logSecurityEvents) {
          logSecurityEvent('localStorage_violation', {
            action: 'cleanup_performed',
            removedKeys: cleanupResult.removed,
            keptKeys: cleanupResult.kept
          });
        }
      }

    } catch (error) {
      
    }
  }

  /**
   * Start periodic security auditing
   */
  private startPeriodicAudit(): void {
    if (this.auditTimer) {
      clearInterval(this.auditTimer);
    }

    this.auditTimer = setInterval(() => {
      this.performAudit();
    }, this.config.auditIntervalMs);

    
  }

  /**
   * Stop periodic security auditing
   */
  stopPeriodicAudit(): void {
    if (this.auditTimer) {
      clearInterval(this.auditTimer);
      this.auditTimer = null;
      
    }
  }

  /**
   * Validate JWT token security
   */
  validateJWTSecurity(token: string): { secure: boolean; issues: string[] } {
    if (!token) {
      return { secure: false, issues: ['No JWT token provided'] };
    }

    const tamperingResult = detectJWTTampering(token);
    
    if (tamperingResult.tampered && this.config.logSecurityEvents) {
      logSecurityEvent('jwt_tampering', {
        issues: tamperingResult.issues,
        tokenLength: token.length,
        timestamp: new Date().toISOString()
      });
    }

    return {
      secure: !tamperingResult.tampered,
      issues: tamperingResult.issues
    };
  }

  /**
   * Validate user permissions
   */
  validateUserPermissions(
    requestedPermissions: string[], 
    jwtClaims: any
  ): { authorized: boolean; violations: string[] } {
    const result = validatePermissions(requestedPermissions, jwtClaims);
    
    if (!result.authorized && this.config.logSecurityEvents) {
      logSecurityEvent('permission_violation', {
        requestedPermissions,
        userPermissions: jwtClaims?.permissions || [],
        violations: result.violations,
        timestamp: new Date().toISOString()
      });
    }

    return result;
  }

  /**
   * Get current security status
   */
  getSecurityStatus(): SecurityStatus {
    return { ...this.status };
  }

  /**
   * Update security configuration
   */
  updateConfig(newConfig: Partial<SecurityConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    // Restart periodic audit if interval changed
    if (newConfig.auditIntervalMs && this.config.enablePeriodicAudit) {
      this.startPeriodicAudit();
    }
    
    // Stop periodic audit if disabled
    if (newConfig.enablePeriodicAudit === false) {
      this.stopPeriodicAudit();
    }
  }

  /**
   * Force immediate security audit
   */
  async forceAudit(): Promise<SecurityStatus> {
    await this.performAudit();
    return this.getSecurityStatus();
  }

  /**
   * Cleanup and shutdown security service
   */
  shutdown(): void {
    this.stopPeriodicAudit();
    this.initialized = false;
    
  }

  /**
   * Check if security service is initialized
   */
  isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * Get security recommendations
   */
  getSecurityRecommendations(): string[] {
    const recommendations: string[] = [];

    if (!this.status.isSecure) {
      recommendations.push('Perform immediate security cleanup');
    }

    if (this.status.issues.length > 0) {
      recommendations.push('Review and resolve security issues');
    }

    if (!this.status.lastAudit || 
        Date.now() - this.status.lastAudit.getTime() > 300000) { // 5 minutes
      recommendations.push('Perform security audit');
    }

    // Note: JWT tokens are now managed in memory by UserStore, not localStorage
    // This is the expected secure behavior - no need to check localStorage for tokens
    
    return recommendations;
  }
}

// Create singleton instance
export const securityService = new SecurityService();

// Export for testing
export { SecurityService };

/**
 * Initialize security service with UserStore integration
 */
export async function initializeSecurityService(config?: Partial<SecurityConfig>): Promise<void> {
  if (config) {
    securityService.updateConfig(config);
  }
  
  await securityService.initialize();
}

/**
 * Validate request permissions (for use in components)
 */
export function validateRequestPermissions(
  permissions: string[], 
  userStore: any
): boolean {
  if (!userStore.token || !userStore.userData) {
    return false;
  }

  const jwtClaims = {
    permissions: userStore.userPermissions
  };

  const result = securityService.validateUserPermissions(permissions, jwtClaims);
  return result.authorized;
}

/**
 * Security middleware for route protection
 */
export function createSecurityMiddleware() {
  return async (to: any, from: any, next: any) => {
    // Perform security check before route navigation
    const status = securityService.getSecurityStatus();
    
    if (!status.isSecure) {
      
      await securityService.performAudit();
    }

    next();
  };
}

/**
 * Security composable for Vue components
 */
export function useSecurity() {
  return {
    securityService,
    validateJWT: (token: string) => securityService.validateJWTSecurity(token),
    validatePermissions: (permissions: string[], claims: any) => 
      securityService.validateUserPermissions(permissions, claims),
    getStatus: () => securityService.getSecurityStatus(),
    forceAudit: () => securityService.forceAudit(),
    getRecommendations: () => securityService.getSecurityRecommendations()
  };
}