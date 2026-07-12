/**
 * Secure Auth Composable
 * 
 * This composable provides a secure authentication interface using the UserStore
 * instead of localStorage. Maintains backward compatibility with existing components.
 * Implements requirements 6.3, 6.4 and JWT lifecycle management 5.1, 5.2, 5.5, 5.6.
 */

import { computed } from 'vue';
import { useUserStore } from '../stores/userStore';

export function useSecureAuth() {
  const userStore = useUserStore();
  
  return {
    // Reactive user data from store (Requirements 6.3, 6.4)
    user: computed(() => userStore.userData),
    token: computed(() => userStore.token),
    isAuthenticated: computed(() => userStore.isAuthenticated),
    
    // Loading and error states
    isLoading: computed(() => userStore.isLoading),
    syncError: computed(() => userStore.syncError),
    lastSync: computed(() => userStore.lastSync),
    
    // Actions - backward compatible API
    login: userStore.loginReactive,
    signup: userStore.signup,
    logout: userStore.logoutReactive,
    refreshUser: userStore.manualRefresh,
    
    // Enhanced actions with reactive updates
    updatePreferences: userStore.updateUserPreferencesReactive,
    refreshToken: userStore.refreshToken,
    initializeUser: userStore.startupSync,
    
    // JWT Lifecycle Management (Requirements 5.1, 5.2, 5.5, 5.6)
    onSessionWarning: userStore.onSessionWarning,
    onSessionExpired: userStore.onSessionExpired,
    clearTokenTimers: userStore.clearTokenTimers,
    
    // Specific user properties for easy access (Requirements 6.3, 6.4)
    userRole: computed(() => userStore.userRole),
    userPermissions: computed(() => userStore.userPermissions),
    showNotificationToasts: computed(() => userStore.showNotificationToasts),
    userEmail: computed(() => userStore.userEmail),
    userName: computed(() => userStore.userName),
    userImage: computed(() => userStore.userImage),
    
    // Reactive update subscription
    onUserDataUpdate: userStore.onUserDataUpdate,
    
    // Utilities
    isTokenExpired: userStore.isTokenExpired,
    decodeJWT: userStore.decodeJWT,
    
    // Legacy methods for backward compatibility
    setToken: (newToken: string) => {
      userStore.token = newToken;
    },
    setUser: async (newUser: any) => {
      // This method is deprecated but maintained for compatibility
      
      if (newUser) {
        await userStore.refreshUserData();
      }
    }
  };
}

// Export as default for easier migration
export default useSecureAuth;