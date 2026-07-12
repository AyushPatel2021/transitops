/**
 * Composable wrapper for the notification store
 * 
 * This provides a composable interface to the shared notification store
 * for components that need reactive access to notification data.
 */

import { computed } from 'vue';
import { notificationStore } from '../stores/notificationStore';

export function useNotificationsStore() {
  return {
    // Reactive state
    notifications: computed(() => notificationStore.state.notifications),
    realtimeNotifications: computed(() => notificationStore.state.realtimeNotifications),
    unreadCount: notificationStore.unreadCount,
    isConnected: computed(() => notificationStore.state.isConnected),
    connectionStatus: computed(() => notificationStore.state.connectionStatus),
    connectionError: computed(() => notificationStore.state.connectionError),
    isReconnecting: computed(() => notificationStore.state.isReconnecting),
    isOnline: computed(() => notificationStore.state.isOnline),
    isPolling: computed(() => notificationStore.state.isPolling),
    fallbackToPolling: computed(() => notificationStore.state.fallbackToPolling),
    
    // Functions
    connectWebSocket: notificationStore.connectWebSocket,
    disconnectWebSocket: notificationStore.disconnectWebSocket,
    fetchRecentNotifications: notificationStore.fetchRecentNotifications,
    markAsRead: notificationStore.markAsRead,
    markAllAsRead: notificationStore.markAllAsRead,
    addLocalNotification: notificationStore.addLocalNotification,
    removeLocalNotification: notificationStore.removeLocalNotification,
    executeNotificationAction: notificationStore.executeNotificationAction
  };
}