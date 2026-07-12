/**
 * Global Notification Manager
 * 
 * This module provides a singleton pattern for managing WebSocket connections
 * to prevent multiple connection attempts and ensure proper initialization.
 */

import { ref } from 'vue';

// Global state to track initialization
const isInitialized = ref(false);
const isInitializing = ref(false);

/**
 * Initialize the notification system
 * This function ensures only one WebSocket connection is created
 */
export async function initializeNotifications(): Promise<void> {
    // Prevent multiple simultaneous initializations
    if (isInitialized.value || isInitializing.value) {
        return;
    }

    isInitializing.value = true;

    try {
        // Import the notification store
        const { connectWebSocket, fetchRecentNotifications } = await import('../stores/notificationStore');
        
        // Fetch initial notifications to populate unread count
        await fetchRecentNotifications();
        
        // Connect WebSocket for real-time updates
        connectWebSocket();
        
        isInitialized.value = true;
        
    } catch (error) {
        // Silent error handling
    } finally {
        isInitializing.value = false;
    }
}

/**
 * Disconnect the notification system
 */
export async function disconnectNotifications(): Promise<void> {
    if (!isInitialized.value) {
        return;
    }

    try {
        // Import the notification store
        const { disconnectWebSocket } = await import('../stores/notificationStore');
        
        // Disconnect WebSocket
        disconnectWebSocket();
        
        // Reset state
        isInitialized.value = false;
        
    } catch (error) {
        // Silent error handling
    }
}

/**
 * Get the current initialization status
 */
export function getNotificationStatus() {
    return {
        isInitialized: isInitialized.value,
        isInitializing: isInitializing.value
    };
}

/**
 * Force reconnect (useful for debugging)
 */
export async function reconnectNotifications(): Promise<void> {
    await disconnectNotifications();
    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
    await initializeNotifications();
}