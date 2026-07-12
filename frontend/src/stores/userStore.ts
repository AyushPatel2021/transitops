/**
 * Secure User Store
 * 
 * This store manages user data in memory only, with JWT tokens stored in localStorage.
 * Implements secure user data management as per requirements 2.1, 2.2, 2.3, 2.5.
 * 
 * Security Features (Requirements 6.2, 6.5, 8.1):
 * - Automatic localStorage cleanup and validation
 * - JWT tampering detection and prevention
 * - Legacy data migration with security audit
 * - Real-time security monitoring
 */

import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import api from '../core/api';
import { securityService } from '../services/securityService';

// User data interfaces
export interface UserRole {
  name: string;
  label: string;
  permissions: string[];
}

export interface UserPreferences {
  show_notification_toasts: boolean;
  theme: string;
  language?: string;
}



export interface UserData {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  preferences: UserPreferences;

  image?: string;
  is_active: boolean;
  last_login_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SignupPayload {
  email: string;
  password: string;
  full_name: string;
  role: 'fleet_manager' | 'driver' | 'safety_officer' | 'financial_analyst';
  contact_number?: string;
  license_number?: string;
  license_category?: 'LMV' | 'HMV' | 'Heavy Truck' | 'Trailer';
  license_expiry_date?: string;
}

// JWT Claims interface
export interface JWTClaims {
  sub: string;           // User email
  user_id: number;       // User ID
  role: string;          // User role name
  permissions: string[]; // User permissions array
  preferences: UserPreferences;

  is_active: boolean;
  exp: number;           // Expiration timestamp
  iat: number;           // Issued at timestamp
}

// Store state interface
interface UserState {
  // JWT token (only thing stored in localStorage)
  token: string | null;
  
  // User data (stored in memory only)
  userData: UserData | null;
  
  // State management
  isLoading: boolean;
  lastSync: Date | null;
  syncError: string | null;
}

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('token'));
  const userData = ref<UserData | null>(null);
  const isLoading = ref(false);
  const lastSync = ref<Date | null>(null);
  const syncError = ref<string | null>(null);
  
  // Initialization state tracking to prevent duplicate calls
  const isInitializing = ref(false);
  const initializationPromise = ref<Promise<void> | null>(null);
  
  // Logout state tracking to prevent duplicate calls
  const isLoggingOut = ref(false);

  // Getters
  const isAuthenticated = computed(() => {
    // If we have a valid token, we're authenticated (userData will be loaded asynchronously)
    return !!token.value && !isTokenExpired(token.value);
  });
  const userRole = computed(() => userData.value?.role?.name);
  const userPermissions = computed(() => userData.value?.role?.permissions || []);
  const showNotificationToasts = computed(() => userData.value?.preferences?.show_notification_toasts ?? true);
  const userEmail = computed(() => userData.value?.email);
  const userName = computed(() => userData.value?.full_name);
  const userImage = computed(() => userData.value?.image);


  // Watch token changes to sync with localStorage
  watch(token, (newToken) => {
    if (newToken) {
      localStorage.setItem('token', newToken);
    } else {
      localStorage.removeItem('token');
    }
  }, { immediate: false });

  // JWT token utilities
  function decodeJWT(token: string): JWTClaims | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      
      return null;
    }
  }

  function isTokenExpired(token: string): boolean {
    if (!token) return true;
    
    const claims = decodeJWT(token);
    if (!claims) return true;
    
    const now = Math.floor(Date.now() / 1000);
    return claims.exp < now;
  }

  // Actions
  async function login(email: string, password: string): Promise<void> {
    isLoading.value = true;
    syncError.value = null;

    try {
      // Perform security validation before login
      await securityService.performAudit();
      
      const response = await api.post('/auth/login', {
        username: email,
        password: password
      });

      const { access_token, user } = response.data;
      
      // Validate JWT token security before storing
      const jwtValidation = securityService.validateJWTSecurity(access_token);
      if (!jwtValidation.secure) {
        throw new Error(`JWT validation failed: ${jwtValidation.issues.join(', ')}`);
      }
      
      // Store JWT token in localStorage
      token.value = access_token;
      
      // Decode JWT to get comprehensive user data
      const claims = decodeJWT(access_token);
      if (claims) {
        // Combine API response with JWT claims for complete user data
        userData.value = {
          id: claims.user_id,
          email: claims.sub,
          full_name: user.full_name || '',
          role: {
            name: claims.role,
            label: user.role?.label || claims.role,
            permissions: claims.permissions
          },
          preferences: claims.preferences,

          image: user.image,
          is_active: claims.is_active,
          last_login_at: user.last_login_at,
          created_at: user.created_at,
          updated_at: user.updated_at
        };
      } else {
        // Fallback to basic user data from API response
        userData.value = {
          id: user.id,
          email: user.email,
          full_name: user.full_name,
          role: {
            name: user.role?.name || 'unassigned',
            label: user.role?.label || 'Unassigned',
            permissions: user.role?.permissions || []
          },
          preferences: {
            show_notification_toasts: user.show_notification_toasts ?? true,
            theme: user.theme || 'light'
          },
          image: user.image,
          is_active: user.is_active ?? true,
          last_login_at: user.last_login_at,
          created_at: user.created_at,
          updated_at: user.updated_at
        };
      }

      lastSync.value = new Date();
      
      // Initialize notification service when user is set
      await initializeNotificationService();
      
      // Connect user data WebSocket for real-time updates
      connectUserDataWebSocket();
      
      // Perform post-login security audit
      await securityService.performAudit();
      
    } catch (error: any) {
      syncError.value = error.response?.data?.detail || 'Login failed';
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function signup(payload: SignupPayload): Promise<void> {
    isLoading.value = true;
    syncError.value = null;

    try {
      // Perform security validation before signup
      await securityService.performAudit();
      
      const response = await api.post('/auth/signup', payload);

      const { access_token, user } = response.data;
      
      // If we got a token back, auto-login the user
      if (access_token) {
        // Validate JWT token security before storing
        const jwtValidation = securityService.validateJWTSecurity(access_token);
        if (!jwtValidation.secure) {
          throw new Error(`JWT validation failed: ${jwtValidation.issues.join(', ')}`);
        }
        
        // Store JWT token in localStorage
        token.value = access_token;
        
        // Decode JWT to get comprehensive user data
        const claims = decodeJWT(access_token);
        if (claims) {
          // Combine API response with JWT claims for complete user data
          userData.value = {
            id: claims.user_id,
            email: claims.sub,
            full_name: user.full_name || '',
            role: {
              name: claims.role,
              label: user.role?.label || claims.role,
              permissions: claims.permissions
            },
            preferences: claims.preferences,

            image: user.image,
            is_active: claims.is_active,
            last_login_at: user.last_login_at,
            created_at: user.created_at,
            updated_at: user.updated_at
          };
        } else {
          // Fallback to basic user data from API response
          userData.value = {
            id: user.id,
            email: user.email,
            full_name: user.full_name,
            role: {
              name: user.role?.name || 'unassigned',
              label: user.role?.label || 'Unassigned',
              permissions: user.role?.permissions || []
            },
            preferences: {
              show_notification_toasts: user.show_notification_toasts ?? true,
              theme: user.theme || 'dark'
            },
            image: user.image,
            is_active: user.is_active ?? true,
            last_login_at: user.last_login_at,
            created_at: user.created_at,
            updated_at: user.updated_at
          };
        }

        lastSync.value = new Date();
        
        // Initialize notification service when user is set
        await initializeNotificationService();
        
        // Connect user data WebSocket for real-time updates
        connectUserDataWebSocket();
        
        // Perform post-signup security audit
        await securityService.performAudit();
      }
    } catch (error: any) {
      syncError.value = error.response?.data?.detail || 'Signup failed';
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  // JWT token lifecycle management (Requirements 5.1, 5.2, 5.5, 5.6)
  const tokenRefreshTimer = ref<number | null>(null);
  const sessionWarningTimer = ref<number | null>(null);
  const sessionWarningShown = ref(false);
  
  // Session timeout warning callbacks
  const sessionWarningCallbacks = new Set<(timeRemaining: number) => void>();
  const sessionExpiredCallbacks = new Set<() => void>();

  function onSessionWarning(callback: (timeRemaining: number) => void): () => void {
    sessionWarningCallbacks.add(callback);
    return () => sessionWarningCallbacks.delete(callback);
  }

  function onSessionExpired(callback: () => void): () => void {
    sessionExpiredCallbacks.add(callback);
    return () => sessionExpiredCallbacks.delete(callback);
  }

  function emitSessionWarning(timeRemaining: number): void {
    sessionWarningCallbacks.forEach(callback => {
      try {
        callback(timeRemaining);
      } catch (error: any) {
        
      }
    });
  }

  function emitSessionExpired(): void {
    sessionExpiredCallbacks.forEach(callback => {
      try {
        callback();
      } catch (error: any) {
        
      }
    });
  }

  // Clear all timers
  function clearTokenTimers(): void {
    if (tokenRefreshTimer.value) {
      clearTimeout(tokenRefreshTimer.value);
      tokenRefreshTimer.value = null;
    }
    if (sessionWarningTimer.value) {
      clearTimeout(sessionWarningTimer.value);
      sessionWarningTimer.value = null;
    }
    sessionWarningShown.value = false;
  }

  // Enhanced logout with server-side token invalidation (Requirements 5.2, 5.6)
  async function logout(): Promise<void> {
    // Prevent multiple simultaneous logout calls
    if (isLoggingOut.value) {
      return;
    }
    
    isLoggingOut.value = true;
    
    try {
      // Clear timers first
      clearTokenTimers();
      
      // Attempt to invalidate token on server
      if (token.value) {
        try {
          await api.post('/auth/logout');
          
        } catch (error) {
          
          // Continue with logout even if server invalidation fails
        }
      }
      
      // Disconnect notification service before clearing auth data
      await disconnectNotificationService();
      
      // Disconnect user data WebSocket
      disconnectUserDataWebSocket();
      
      // Clear token and user data
      token.value = null;
      userData.value = null;
      lastSync.value = null;
      syncError.value = null;
      
      // Clear cache
      userDataCache.value = {
        data: null,
        timestamp: 0,
        version: 0
      };
      
      
    } finally {
      isLoggingOut.value = false;
    }
  }

  async function refreshUserData(): Promise<void> {
    if (!token.value) {
      throw new Error('No authentication token available');
    }

    // Check if token is expired
    if (isTokenExpired(token.value)) {
      await logout();
      throw new Error('Token expired');
    }

    isLoading.value = true;
    syncError.value = null;

    try {
      
      const response = await api.get('/profile');
      const profileData = response.data.data || response.data;
      
      // Decode JWT to get comprehensive user data
      const claims = decodeJWT(token.value);
      
      if (userData.value) {
        
        // Update existing user data with fresh data from server
        const updatedUserData = {
          ...userData.value,
          full_name: profileData.full_name || userData.value.full_name,
          image: profileData.image,
          preferences: {
            ...userData.value.preferences,
            ...profileData.preferences
          },
          role: {
            name: profileData.role?.name || userData.value.role?.name || 'unassigned',
            label: profileData.role?.label || userData.value.role?.label || profileData.role?.name || 'Unassigned',
            permissions: profileData.role?.permissions || userData.value.role?.permissions || []
          },
          last_login_at: profileData.last_login_at,
          updated_at: profileData.updated_at
        };
        
        // Replace the entire userData object to ensure reactivity
        userData.value = updatedUserData;
        
      } else {
        
        // Initialize user data from JWT claims and profile data (for refresh scenarios)
        if (claims) {
          userData.value = {
            id: claims.user_id,
            email: claims.sub,
            full_name: profileData.full_name || '',
            role: {
              name: claims.role,
              label: profileData.role?.label || claims.role,
              permissions: claims.permissions
            },
            preferences: {
              ...claims.preferences,
              ...profileData.preferences
            },

            image: profileData.image,
            is_active: claims.is_active,
            last_login_at: profileData.last_login_at,
            created_at: profileData.created_at,
            updated_at: profileData.updated_at
          };
        } else {
          // Fallback to basic user data from API response
          userData.value = {
            id: profileData.id,
            email: profileData.email,
            full_name: profileData.full_name,
            role: {
              name: profileData.role?.name || 'unassigned',
              label: profileData.role?.label || 'Unassigned',
              permissions: profileData.role?.permissions || []
            },
            preferences: {
              show_notification_toasts: profileData.show_notification_toasts ?? true,
              theme: profileData.theme || 'light',
              ...profileData.preferences
            },
            image: profileData.image,
            is_active: profileData.is_active ?? true,
            last_login_at: profileData.last_login_at,
            created_at: profileData.created_at,
            updated_at: profileData.updated_at
          };
        }
        
      }

      lastSync.value = new Date();
      
      // Emit user data update event for reactive UI updates
      
      emitUserDataUpdate('data_refreshed');
      
      // Force Vue reactivity by triggering a nextTick update
      await new Promise(resolve => setTimeout(resolve, 0));
      
      
    } catch (error: any) {
      syncError.value = error.response?.data?.detail || 'Failed to refresh user data';
      
      // If unauthorized, logout user
      if (error.response?.status === 401) {
        await logout();
      }
      
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function updateUserPreferences(preferences: Partial<UserPreferences>): Promise<void> {
    if (!userData.value) {
      throw new Error('No user data available');
    }

    // Update preferences in memory immediately for reactive UI
    userData.value.preferences = {
      ...userData.value.preferences,
      ...preferences
    };

    // Sync with server in background
    try {
      await api.patch('/profile', { preferences });
      lastSync.value = new Date();
    } catch (error: any) {
      syncError.value = error.response?.data?.detail || 'Failed to update preferences';
      
      // Optionally revert changes on error
      await refreshUserData();
      throw error;
    }
  }

  async function refreshToken(): Promise<void> {
    if (!token.value) {
      throw new Error('No token to refresh');
    }

    try {
      const response = await api.post('/auth/refresh-token');
      token.value = response.data.access_token;
      
      // Broadcast token refresh to other tabs
      broadcastUserDataUpdate('token_refreshed', {
        token: response.data.access_token,
        timestamp: new Date().toISOString()
      });
      
      // Update user data from new JWT claims
      const claims = decodeJWT(response.data.access_token);
      if (claims && userData.value) {
        userData.value.role = {
          name: claims.role,
          label: userData.value.role?.label || claims.role,
          permissions: claims.permissions
        };
        userData.value.preferences = claims.preferences;
        userData.value.is_active = claims.is_active;
        
        // Update cache
        if (userData.value) {
          userDataCache.value = {
            data: { ...userData.value },
            timestamp: Date.now(),
            version: userDataCache.value.version + 1
          };
        }
        
        // Broadcast user data update to other tabs
        broadcastUserDataUpdate('user_data_updated', {
          userData: userData.value,
          timestamp: new Date().toISOString()
        });
      }
      
      lastSync.value = new Date();
      sessionWarningShown.value = false; // Reset warning flag
      
      
    } catch (error: any) {
      syncError.value = error.response?.data?.detail || 'Failed to refresh token';
      
      // If refresh fails, logout user
      if (error.response?.status === 401) {
        
        await logoutReactive();
      }
      
      throw error;
    }
  }

  // Initialize user data on app startup
  async function initializeUser(): Promise<void> {
    // If already initializing, return the existing promise to prevent duplicate calls
    if (isInitializing.value && initializationPromise.value) {
      return initializationPromise.value;
    }
    
    if (!token.value) {
      return;
    }

    // Check if token is expired first
    if (isTokenExpired(token.value)) {
      
      await logout();
      return;
    }

    // Validate JWT token security before proceeding
    const jwtValidation = securityService.validateJWTSecurity(token.value);
    if (!jwtValidation.secure) {
      
      await logout();
      return;
    }

    // If we already have user data and it's recent, don't fetch again
    if (userData.value && lastSync.value && (Date.now() - lastSync.value.getTime()) < 60000) {
      
      return;
    }

    // Set initialization state and create promise
    isInitializing.value = true;
    initializationPromise.value = (async () => {
      try {
        isLoading.value = true;
        await refreshUserData();
        await initializeNotificationService();
        
        // Setup token refresh after successful initialization
        setupTokenRefresh();
        
        // Perform security audit after initialization
        await securityService.performAudit();
        
        // Emit initialization completion event
        emitUserDataUpdate('initialization_completed');
        
        
      } catch (error: any) {
        
        
        // If it's an auth error, logout
        if (error.response?.status === 401) {
          await logout();
          throw error;
        }
        
        // For other errors, don't throw to avoid blocking the app
        syncError.value = 'Failed to load user data';
      } finally {
        isLoading.value = false;
        isInitializing.value = false;
        initializationPromise.value = null;
      }
    })();
    
    return initializationPromise.value;
  }

  // Notification service integration
  async function initializeNotificationService(): Promise<void> {
    if (!userData.value || !token.value) {
      return;
    }

    try {
      const { initializeNotifications } = await import('../core/notificationManager');
      await initializeNotifications();
    } catch (error) {
      
    }
  }

  async function disconnectNotificationService(): Promise<void> {
    try {
      const { disconnectNotifications } = await import('../core/notificationManager');
      await disconnectNotifications();
    } catch (error) {
      
    }
  }

  // User data synchronization methods (Requirements 2.3, 2.4, 4.1, 4.6)
  
  // Automatic user data refresh on app startup
  async function startupSync(): Promise<void> {
    if (!token.value) {
      return;
    }

    
    
    try {
      // Check token validity first
      if (isTokenExpired(token.value)) {
        
        await logout();
        return;
      }

      // Initialize user data from server
      await refreshUserData();
      
      
      // Setup automatic refresh and notification service
      setupTokenRefresh();
      await initializeNotificationService();
      
      // Emit startup completion event
      emitUserDataUpdate('startup_completed');
      
    } catch (error) {
      
      // Don't logout on startup sync failure, just log the error
    }
  }

  // Manual refresh mechanism for user data updates
  async function manualRefresh(): Promise<void> {
    
    
    if (!token.value) {
      throw new Error('No authentication token available for manual refresh');
    }

    try {
      await refreshUserData();
      
      
      // Emit event for reactive UI updates
      emitUserDataUpdate('manual_refresh');
      
    } catch (error) {
      
      throw error;
    }
  }

  // Reactive user data updates for UI components
  const userDataUpdateCallbacks = new Set<(eventType: string, userData: UserData | null) => void>();

  function onUserDataUpdate(callback: (eventType: string, userData: UserData | null) => void): () => void {
    userDataUpdateCallbacks.add(callback);
    
    // Return unsubscribe function
    return () => {
      userDataUpdateCallbacks.delete(callback);
    };
  }

  function emitUserDataUpdate(eventType: string): void {
    
    
    userDataUpdateCallbacks.forEach(callback => {
      try {
        callback(eventType, userData.value);
      } catch (error) {
        
      }
    });
  }

  // Enhanced user preference updates with real-time synchronization
  async function updateUserPreferencesReactive(preferences: Partial<UserPreferences>): Promise<void> {
    if (!userData.value) {
      throw new Error('No user data available');
    }

    const oldPreferences = { ...userData.value.preferences };

    // Update preferences in memory immediately for reactive UI
    userData.value.preferences = {
      ...userData.value.preferences,
      ...preferences
    };

    
    
    // Update cache
    if (userData.value) {
      userDataCache.value = {
        data: { ...userData.value },
        timestamp: Date.now(),
        version: userDataCache.value.version + 1
      };
    }
    
    // Broadcast to other tabs immediately
    broadcastUserDataUpdate('user_preferences_updated', {
      preferences,
      timestamp: new Date().toISOString()
    });
    
    // Emit reactive update event
    emitUserDataUpdate('preferences_updated');

    // Sync with server in background
    try {
      await api.patch('/profile', { preferences });
      lastSync.value = new Date();
      
      
      // Emit sync completion event
      emitUserDataUpdate('preferences_synced');
      
    } catch (error: any) {
      
      
      // Revert changes on error
      if (userData.value) {
        userData.value.preferences = oldPreferences;
        
        // Update cache with reverted data
        if (userData.value) {
          userDataCache.value = {
            data: { ...userData.value },
            timestamp: Date.now(),
            version: userDataCache.value.version + 1
          };
        }
        
        // Broadcast revert to other tabs
        broadcastUserDataUpdate('user_preferences_updated', {
          preferences: oldPreferences,
          timestamp: new Date().toISOString()
        });
        
        emitUserDataUpdate('preferences_reverted');
      }
      
      syncError.value = error.response?.data?.detail || 'Failed to update preferences';
      throw error;
    }
  }

  // Performance optimization: Intelligent caching strategies (Requirements 4.4, 5.1)
  const userDataCache = ref<{
    data: UserData | null;
    timestamp: number;
    version: number;
  }>({
    data: null,
    timestamp: 0,
    version: 0
  });

  const cacheConfig = {
    maxAge: 5 * 60 * 1000, // 5 minutes cache validity
    backgroundRefreshThreshold: 2 * 60 * 1000, // Refresh in background if older than 2 minutes
    maxRetries: 3,
    retryDelay: 1000 // Start with 1 second, exponential backoff
  };

  // Background refresh state
  const backgroundRefreshState = ref({
    isRefreshing: false,
    lastRefreshAttempt: 0,
    retryCount: 0
  });

  // Intelligent cache management
  function isCacheValid(): boolean {
    const now = Date.now();
    const cacheAge = now - userDataCache.value.timestamp;
    return cacheAge < cacheConfig.maxAge && userDataCache.value.data !== null;
  }

  function shouldBackgroundRefresh(): boolean {
    const now = Date.now();
    const cacheAge = now - userDataCache.value.timestamp;
    return cacheAge > cacheConfig.backgroundRefreshThreshold && 
           !backgroundRefreshState.value.isRefreshing &&
           userDataCache.value.data !== null;
  }

  // Background token refresh to prevent interruptions (Requirements 5.1)
  async function backgroundTokenRefresh(): Promise<void> {
    if (!token.value || backgroundRefreshState.value.isRefreshing) {
      return;
    }

    const claims = decodeJWT(token.value);
    if (!claims) return;

    const now = Math.floor(Date.now() / 1000);
    const timeUntilExpiry = claims.exp - now;
    
    // Only refresh if token expires within 10 minutes
    if (timeUntilExpiry > 600) {
      return;
    }

    backgroundRefreshState.value.isRefreshing = true;
    backgroundRefreshState.value.lastRefreshAttempt = Date.now();

    try {
      
      await refreshToken();
      backgroundRefreshState.value.retryCount = 0;
      
    } catch (error) {
      backgroundRefreshState.value.retryCount++;
      
      
      // If we've exceeded max retries, don't try again
      if (backgroundRefreshState.value.retryCount >= cacheConfig.maxRetries) {
        
      }
    } finally {
      backgroundRefreshState.value.isRefreshing = false;
    }
  }

  // Optimized user data fetching with intelligent caching
  async function optimizedRefreshUserData(): Promise<void> {
    // Check if we can use cached data
    if (isCacheValid()) {
      
      if (userDataCache.value.data) {
        userData.value = { ...userDataCache.value.data };
      }
      
      // Schedule background refresh if needed
      if (shouldBackgroundRefresh()) {
        setTimeout(() => backgroundRefreshUserData(), 100);
      }
      
      return;
    }

    // Cache is invalid, fetch fresh data
    await refreshUserData();
    
    // Update cache
    if (userData.value) {
      userDataCache.value = {
        data: { ...userData.value },
        timestamp: Date.now(),
        version: userDataCache.value.version + 1
      };
    }
  }

  // Background user data refresh
  async function backgroundRefreshUserData(): Promise<void> {
    if (backgroundRefreshState.value.isRefreshing) {
      return;
    }

    backgroundRefreshState.value.isRefreshing = true;
    
    try {
      
      await refreshUserData();
      
      // Update cache
      if (userData.value) {
        userDataCache.value = {
          data: { ...userData.value },
          timestamp: Date.now(),
          version: userDataCache.value.version + 1
        };
      }
      
      backgroundRefreshState.value.retryCount = 0;
      
    } catch (error) {
      backgroundRefreshState.value.retryCount++;
      
    } finally {
      backgroundRefreshState.value.isRefreshing = false;
    }
  }

  // Enhanced automatic token refresh with session warnings (Requirements 5.1, 5.5)
  function setupTokenRefresh(): void {
    if (!token.value) return;

    // Clear existing timers
    clearTokenTimers();

    const claims = decodeJWT(token.value);
    if (!claims) return;

    const now = Math.floor(Date.now() / 1000);
    const timeUntilExpiry = claims.exp - now;
    
    // Session warning time (5 minutes before expiry)
    const warningTime = Math.max(timeUntilExpiry - 300, 0);
    
    // Token refresh time (3 minutes before expiry for better performance, minimum 30 seconds)
    const refreshTime = Math.max(timeUntilExpiry - 180, 30);

    
    
    

    // Setup session warning
    if (warningTime > 0 && !sessionWarningShown.value) {
      sessionWarningTimer.value = setTimeout(() => {
        sessionWarningShown.value = true;
        const remainingTime = Math.max(claims.exp - Math.floor(Date.now() / 1000), 0);
        
        emitSessionWarning(remainingTime);
      }, warningTime * 1000);
    }

    // Setup automatic token refresh with background processing
    if (refreshTime > 0) {
      tokenRefreshTimer.value = setTimeout(async () => {
        try {
          
          await backgroundTokenRefresh();
          setupTokenRefresh(); // Setup next refresh
          emitUserDataUpdate('token_refreshed');
        } catch (error) {
          
          
          // If refresh fails, emit session expired and logout
          emitSessionExpired();
          await logoutReactive();
        }
      }, refreshTime * 1000);
    } else {
      // Token is about to expire or already expired
      
      emitSessionExpired();
      setTimeout(() => logoutReactive(), 1000);
    }
  }

  // Enhanced login with reactive updates
  async function loginReactive(email: string, password: string): Promise<void> {
    await login(email, password);
    emitUserDataUpdate('login_completed');
  }

  // Enhanced logout with cleanup and broadcasting
  async function logoutReactive(): Promise<void> {
    // Broadcast logout to other tabs first
    broadcastUserDataUpdate('user_logout', {
      timestamp: new Date().toISOString()
    });
    
    await logout();
    emitUserDataUpdate('logout_completed');
  }

  // Real-time user data synchronization (Requirements 7.3, 7.4, 7.6)
  
  // WebSocket connection for user data updates
  let userDataWebSocket: WebSocket | null = null;
  const wsReconnectAttempts = ref(0);
  const maxWsReconnectAttempts = 5;
  const wsReconnectDelay = ref(1000); // Start with 1 second
  
  // Multi-tab synchronization using BroadcastChannel
  const broadcastChannel = new BroadcastChannel('user-data-sync');
  const tabId = `tab-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  // Listen for user data updates from other tabs
  broadcastChannel.addEventListener('message', (event) => {
    const { type, data, sourceTabId } = event.data;
    
    // Ignore messages from the same tab
    if (sourceTabId === tabId) {
      return;
    }
    
    
    
    switch (type) {
      case 'user_data_updated':
        if (data.userData) {
          userData.value = { ...data.userData };
          lastSync.value = new Date(data.timestamp);
          
          emitUserDataUpdate('cross_tab_sync');
        }
        break;
        
      case 'user_preferences_updated':
        if (userData.value && data.preferences) {
          userData.value.preferences = { ...userData.value.preferences, ...data.preferences };
          
          emitUserDataUpdate('cross_tab_preferences_sync');
        }
        break;
        
      case 'user_logout':
        
        // Perform logout without broadcasting to avoid loops
        performLogoutWithoutBroadcast();
        break;
        
      case 'token_refreshed':
        if (data.token) {
          token.value = data.token;
          
          emitUserDataUpdate('cross_tab_token_refresh');
        }
        break;
    }
  });

  // Broadcast user data changes to other tabs
  function broadcastUserDataUpdate(type: string, data: any): void {
    try {
      broadcastChannel.postMessage({
        type,
        data,
        sourceTabId: tabId,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      
    }
  }

  // WebSocket connection for real-time user data updates
  function connectUserDataWebSocket(): void {
    if (!token.value || !userData.value) {
      
      return;
    }

    // Prevent multiple connections
    if (userDataWebSocket && 
        (userDataWebSocket.readyState === WebSocket.CONNECTING || 
         userDataWebSocket.readyState === WebSocket.OPEN)) {
      
      return;
    }

    // Clean up existing connection
    if (userDataWebSocket) {
      userDataWebSocket.close();
      userDataWebSocket = null;
    }

    try {
      const getWebSocketUrl = () => {
        const envApiUrl = import.meta.env.VITE_API_URL;
        if (envApiUrl) {
          const wsUrl = envApiUrl.replace(/^https?:/, window.location.protocol === 'https:' ? 'wss:' : 'ws:');
          return `${wsUrl}/api/v1/ws/user-data`;
        }
        
        const currentHost = window.location.hostname;
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          return `${wsProtocol}//localhost:8000/api/v1/ws/user-data`;
        }
        
        return `${wsProtocol}//localhost:8000/api/v1/ws/user-data`;
      };

      const wsUrl = `${getWebSocketUrl()}?token=${token.value}`;
      
      
      userDataWebSocket = new WebSocket(wsUrl);

      userDataWebSocket.onopen = () => {
        
        wsReconnectAttempts.value = 0;
        wsReconnectDelay.value = 1000;
      };

      userDataWebSocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleUserDataWebSocketMessage(message);
        } catch (error) {
          
        }
      };

      userDataWebSocket.onclose = (event) => {
        
        userDataWebSocket = null;
        
        // Attempt reconnection if not a normal closure
        if (event.code !== 1000 && wsReconnectAttempts.value < maxWsReconnectAttempts) {
          setTimeout(() => {
            wsReconnectAttempts.value++;
            wsReconnectDelay.value = Math.min(wsReconnectDelay.value * 2, 30000); // Max 30 seconds
            
            connectUserDataWebSocket();
          }, wsReconnectDelay.value);
        }
      };

      userDataWebSocket.onerror = (error) => {
        
      };

    } catch (error) {
      
    }
  }

  // Handle WebSocket messages for user data updates
  function handleUserDataWebSocketMessage(message: any): void {
    const { type, data } = message;
    
    
    
    switch (type) {
      case 'user_data_updated':
        if (data.user_id === userData.value?.id) {
          
          
          // Update user data in memory
          if (userData.value) {
            userData.value = {
              ...userData.value,
              ...data.updates
            };
            
            // Update cache
            if (userData.value) {
              userDataCache.value = {
                data: { ...userData.value },
                timestamp: Date.now(),
                version: userDataCache.value.version + 1
              };
            }
            
            lastSync.value = new Date();
            
            // Broadcast to other tabs
            broadcastUserDataUpdate('user_data_updated', {
              userData: userData.value,
              timestamp: lastSync.value.toISOString()
            });
            
            emitUserDataUpdate('websocket_user_data_updated');
          }
        }
        break;
        
      case 'user_preferences_updated':
        if (data.user_id === userData.value?.id && userData.value) {
          
          
          userData.value.preferences = {
            ...userData.value.preferences,
            ...data.preferences
          };
          
          // Update cache
          if (userData.value) {
            userDataCache.value = {
              data: { ...userData.value },
              timestamp: Date.now(),
              version: userDataCache.value.version + 1
            };
          }
          
          // Broadcast to other tabs
          broadcastUserDataUpdate('user_preferences_updated', {
            preferences: data.preferences,
            timestamp: new Date().toISOString()
          });
          
          emitUserDataUpdate('websocket_preferences_updated');
        }
        break;
        
      case 'user_role_changed':
        if (data.user_id === userData.value?.id) {
          
          
          // This is a critical change that requires token refresh
          setTimeout(async () => {
            try {
              await refreshToken();
              
              emitUserDataUpdate('role_permission_changed');
            } catch (error) {
              
              // Force logout if token refresh fails
              await logoutReactive();
            }
          }, 100);
        }
        break;
        
      case 'user_deactivated':
        if (data.user_id === userData.value?.id) {
          
          
          // Force logout immediately
          setTimeout(() => {
            logoutReactive();
          }, 100);
        }
        break;
        
      case 'force_logout':
        if (data.user_id === userData.value?.id) {
          
          
          // Force logout immediately
          setTimeout(() => {
            logoutReactive();
          }, 100);
        }
        break;
    }
  }

  // Disconnect user data WebSocket
  function disconnectUserDataWebSocket(): void {
    if (userDataWebSocket) {
      userDataWebSocket.close(1000, 'User logout');
      userDataWebSocket = null;
      
    }
  }

  // Logout without broadcasting (to avoid loops in multi-tab scenarios)
  async function performLogoutWithoutBroadcast(): Promise<void> {
    // Clear timers first
    clearTokenTimers();
    
    // Disconnect WebSocket
    disconnectUserDataWebSocket();
    
    // Clear token and user data
    token.value = null;
    userData.value = null;
    lastSync.value = null;
    syncError.value = null;
    
    // Clear cache
    userDataCache.value = {
      data: null,
      timestamp: 0,
      version: 0
    };
    
    
  }

  // Setup automatic token refresh on store initialization
  if (token.value && !isTokenExpired(token.value)) {
    setupTokenRefresh();
  }

  return {
    // State
    token,
    userData,
    isLoading,
    lastSync,
    syncError,
    isInitializing,
    
    // Getters
    isAuthenticated,
    userRole,
    userPermissions,
    showNotificationToasts,
    userEmail,
    userName,
    userImage,
    
    // Actions
    login,
    signup,
    logout,
    refreshUserData,
    updateUserPreferences,
    refreshToken,
    initializeUser,
    
    // Synchronization methods (Requirements 2.3, 2.4, 4.1, 4.6)
    startupSync,
    manualRefresh,
    onUserDataUpdate,
    updateUserPreferencesReactive,
    loginReactive,
    logoutReactive,
    
    // Performance optimizations (Requirements 4.4, 5.1)
    optimizedRefreshUserData,
    backgroundRefreshUserData,
    backgroundTokenRefresh,
    
    // Real-time synchronization (Requirements 7.3, 7.4, 7.6)
    connectUserDataWebSocket,
    disconnectUserDataWebSocket,
    broadcastUserDataUpdate,
    
    // JWT Lifecycle Management (Requirements 5.1, 5.2, 5.5, 5.6)
    onSessionWarning,
    onSessionExpired,
    clearTokenTimers,
    
    // Utilities
    decodeJWT,
    isTokenExpired,
    
    // Internal methods (for testing)
    emitUserDataUpdate,
    emitSessionWarning,
    emitSessionExpired
  };
});
