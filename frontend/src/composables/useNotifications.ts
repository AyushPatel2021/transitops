
/**
 * Legacy useNotifications composable
 * 
 * This provides backward compatibility for components that still use the old API.
 * It wraps the new notification store to maintain the same interface.
 */

import { computed } from 'vue';
import { notificationStore } from '../stores/notificationStore';

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'success' | 'warning' | 'danger' | 'info';
  sticky: boolean;
  duration?: number;
}

export interface NotificationAction {
  type: 'navigate' | 'modal' | 'function';
  target?: string;
  params?: Record<string, any>;
  function_name?: string;
}

export interface RealtimeNotification extends Notification {
  server_id: string;
  action?: NotificationAction;
  read: boolean;
  created_at: string;
  user_id: number;
}

type LegacyNotificationInput = Partial<Pick<Notification, 'title' | 'sticky' | 'duration'>> & {
  message: string;
  type: Notification['type'];
};

export function useNotifications() {
  const add = (notification: LegacyNotificationInput) => {
    return notificationStore.addLocalNotification({
      title: notification.title || 'Notification',
      message: notification.message,
      type: notification.type,
      sticky: notification.sticky ?? false,
      duration: notification.duration
    });
  };

  return {
    // Local notifications (for backward compatibility)
    notifications: computed(() => notificationStore.state.notifications),
    add,
    remove: notificationStore.removeLocalNotification,
    handleAction: (action: any) => {
      if (action && action.tag === 'display_notification') {
        const params = action.params || {};
        notificationStore.addLocalNotification({
          title: params.title || 'Notification',
          message: params.message || '',
          type: params.type || 'info',
          sticky: params.sticky || false
        });
      }
    },
    
    // Real-time notifications
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
    executeNotificationAction: notificationStore.executeNotificationAction
  };
}
