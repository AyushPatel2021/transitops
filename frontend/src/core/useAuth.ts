/**
 * Legacy Auth Composable - Updated for Secure User Data Management
 * 
 * This composable has been updated to use the secure UserStore instead of localStorage
 * while maintaining backward compatibility for existing components.
 * 
 * MIGRATION NOTE: This provides backward compatibility during the transition.
 * New components should use useSecureAuth() directly.
 * 
 * Requirements addressed: 6.1, 6.3, 6.4
 */

import { computed } from 'vue';
import { useUserStore } from '../stores/userStore';

export function useAuth() {
    const userStore = useUserStore();
    
    // Backward compatible computed properties
    const user = computed(() => userStore.userData);
    const token = computed(() => userStore.token);
    const isAuthenticated = computed(() => userStore.isAuthenticated);
    
    // Backward compatible methods that delegate to UserStore
    const setToken = (newToken: string) => {
        userStore.token = newToken;
    };
    
    const setUser = async (newUser: any) => {
        // This method is deprecated but maintained for compatibility
        
        // If a user is being set, refresh the user data from server
        if (newUser && userStore.token) {
            try {
                await userStore.refreshUserData();
            } catch (error) {
                // Silent error handling
            }
        }
    };
    
    const login = async (email: string, password: string) => {
        await userStore.loginReactive(email, password);
    };

    const signup = async (email: string, password: string, fullName: string) => {
        await userStore.signup(email, password, fullName);
    };
    
    const logout = async () => {
        await userStore.logoutReactive();
    };

    const refreshUser = async () => {
        await userStore.manualRefresh();
    };

    return { 
        user, 
        token,
        isAuthenticated, 
        login, 
        signup, 
        logout, 
        setToken, 
        setUser,
        refreshUser
    };
}
