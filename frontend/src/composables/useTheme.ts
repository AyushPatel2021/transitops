/**
 * Theme Management Composable
 * 
 * Handles theme switching, persistence, and system preference detection.
 * Integrates with user preferences and provides reactive theme state.
 */

import { ref, computed, watch, onMounted } from 'vue';
import { useUserStore } from '../stores/userStore';

export type ThemeMode = 'light' | 'dark' | 'auto';

export const useTheme = () => {
  const userStore = useUserStore();
  
  // Current theme mode from user preferences or default
  const currentTheme = computed<ThemeMode>(() => {
    return (userStore.userData?.preferences?.theme as ThemeMode) || 'light';
  });
  
  // Resolved theme (what's actually applied)
  const resolvedTheme = ref<'light' | 'dark'>('light');
  
  // System theme preference
  const systemTheme = ref<'light' | 'dark'>('light');
  
  // Check if system prefers dark mode
  const updateSystemTheme = () => {
    systemTheme.value = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };
  
  // Apply theme to document
  const applyTheme = (theme: ThemeMode) => {
    const root = document.documentElement;
    
    // Remove existing theme attributes
    root.removeAttribute('data-theme');
    
    // Apply new theme
    root.setAttribute('data-theme', theme);
    
    // Update resolved theme
    if (theme === 'auto') {
      resolvedTheme.value = systemTheme.value;
    } else {
      resolvedTheme.value = theme;
    }
    
    // Store in localStorage as fallback
    localStorage.setItem('theme-preference', theme);
    
  };
  
  // Update theme when user preferences change
  watch(currentTheme, (newTheme) => {
    applyTheme(newTheme);
  }, { immediate: false });
  
  // Watch system theme changes for auto mode
  watch(systemTheme, (newSystemTheme) => {
    if (currentTheme.value === 'auto') {
      resolvedTheme.value = newSystemTheme;
      // Re-apply auto theme to trigger CSS updates
      applyTheme('auto');
    }
  });
  
  // Change theme and update user preferences
  const setTheme = async (theme: ThemeMode) => {
    try {
      // Update user preferences if authenticated
      if (userStore.isAuthenticated && userStore.userData) {
        await userStore.updateUserPreferencesReactive({
          theme
        });
      } else {
        // Store locally if not authenticated
        localStorage.setItem('theme-preference', theme);
        applyTheme(theme);
      }
    } catch (error) {
      console.error('Failed to update theme preference:', error);
      // Apply theme locally even if server update fails
      applyTheme(theme);
    }
  };
  
  // Initialize theme system
  const initializeTheme = () => {
    // Update system theme
    updateSystemTheme();
    
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', updateSystemTheme);
    
    // Apply initial theme
    if (userStore.isAuthenticated && userStore.userData?.preferences?.theme) {
      // Use user preference
      applyTheme(userStore.userData.preferences.theme as ThemeMode);
    } else {
      // Use localStorage fallback or default
      const savedTheme = localStorage.getItem('theme-preference') as ThemeMode;
      applyTheme(savedTheme || 'light');
    }
    
  };
  
  // Get theme icon for UI
  const getThemeIcon = (theme: ThemeMode) => {
    switch (theme) {
      case 'light':
        return '☀️';
      case 'dark':
        return '🌙';
      case 'auto':
        return '🔄';
      default:
        return '☀️';
    }
  };
  
  // Get theme label for UI
  const getThemeLabel = (theme: ThemeMode) => {
    switch (theme) {
      case 'light':
        return 'Light';
      case 'dark':
        return 'Dark';
      case 'auto':
        return 'Auto (System)';
      default:
        return 'Light';
    }
  };
  
  // Check if theme is dark (for conditional styling)
  const isDark = computed(() => resolvedTheme.value === 'dark');
  
  // Available theme options
  const themeOptions: ThemeMode[] = ['light', 'dark', 'auto'];
  
  return {
    // State
    currentTheme,
    resolvedTheme,
    systemTheme,
    isDark,
    themeOptions,
    
    // Actions
    setTheme,
    initializeTheme,
    applyTheme,
    
    // Utilities
    getThemeIcon,
    getThemeLabel
  };
};