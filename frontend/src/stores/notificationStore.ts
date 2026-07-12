/**
 * Shared Notification Store
 * 
 * This provides a global reactive store for notifications that can be used
 * across components without creating multiple WebSocket connections.
 */

import { computed, reactive } from 'vue';
import { useUserStore } from './userStore';
import api from '../core/api';

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'success' | 'warning' | 'danger' | 'info';
  sticky: boolean;
  duration?: number;
}

export interface RealtimeNotification extends Notification {
  server_id: string;
  action?: {
    type: 'navigate' | 'modal' | 'function';
    target?: string;
    params?: Record<string, any>;
    function_name?: string;
  };
  read: boolean;
  created_at: string;
  user_id: number;
}

interface WebSocketMessage {
  type: 'notification' | 'notification_read' | 'notifications_read_all' | 'heartbeat' | 'heartbeat_response' | 'connection_established' | 'error';
  data: any;
  timestamp: string;
}

// Global reactive state
const state = reactive({
  // Local notifications (toast-style)
  notifications: [] as Notification[],
  
  // Real-time notifications from server
  realtimeNotifications: [] as RealtimeNotification[],
  
  // Connection state
  isConnected: false,
  connectionStatus: 'disconnected' as 'connected' | 'connecting' | 'disconnected' | 'error' | 'reconnecting',
  connectionError: null as string | null,
  isReconnecting: false,
  isOnline: navigator.onLine,
  isPolling: false,
  fallbackToPolling: false,
});

// WebSocket connection management
let websocket: WebSocket | null = null;
let reconnectAttempts = 0;
let reconnectTimeout: number | null = null;
let heartbeatInterval: number | null = null;
let heartbeatTimeout: number | null = null;
let pollingInterval: number | null = null;
let nextId = 1;

const maxReconnectAttempts = 10;

// Computed properties
export const unreadCount = computed(() => {
  return state.realtimeNotifications.filter((n: RealtimeNotification) => !n.read).length;
});

// WebSocket connection functions
export function connectWebSocket() {
  const userStore = useUserStore();
  
  if (!userStore.userData || !userStore.token) {
    state.connectionError = 'Authentication required';
    state.connectionStatus = 'error';
    return;
  }

  // Prevent multiple simultaneous connection attempts
  if (websocket && (websocket.readyState === WebSocket.CONNECTING || websocket.readyState === WebSocket.OPEN)) {
    return;
  }

  // Clean up any existing connection first
  if (websocket) {
    websocket.close();
    websocket = null;
  }

  state.connectionStatus = state.isReconnecting ? 'reconnecting' : 'connecting';
  state.connectionError = null;

  try {
    const getWebSocketUrl = () => {
      const envApiUrl = import.meta.env.VITE_API_URL;
      if (envApiUrl) {
        const wsUrl = envApiUrl.replace(/^https?:/, window.location.protocol === 'https:' ? 'wss:' : 'ws:');
        return `${wsUrl}/api/v1/ws/notifications`;
      }
      
      const currentHost = window.location.hostname;
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      
      if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
        return `${wsProtocol}//localhost:8000/api/v1/ws/notifications`;
      }
      
      if (currentHost.match(/^192\.168\.\d+\.\d+$/) || currentHost.match(/^10\.\d+\.\d+\.\d+$/)) {
        return `${wsProtocol}//${currentHost}:8000/api/v1/ws/notifications`;
      }
      
      if (currentHost.includes('ngrok')) {
        return `${wsProtocol}//${currentHost}/api/v1/ws/notifications`;
      }
      
      return `${wsProtocol}//localhost:8000/api/v1/ws/notifications`;
    };
    
    const wsUrl = `${getWebSocketUrl()}?token=${userStore.token}`;
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      state.isConnected = true;
      state.connectionStatus = 'connected';
      state.connectionError = null;
      reconnectAttempts = 0;
      state.isReconnecting = false;
      
      startHeartbeat();
      
      if (reconnectAttempts > 0) {
        syncMissedNotifications();
      }
    };
    
    websocket.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleWebSocketMessage(message);
        resetHeartbeatTimeout();
      } catch (error) {
        state.connectionError = 'Message parsing error';
      }
    };
    
    websocket.onclose = (event) => {
      state.isConnected = false;
      state.connectionStatus = 'disconnected';
      websocket = null;
      
      stopHeartbeat();
      
      if (event.code === 1000) {
        state.connectionError = null;
        return;
      }
      
      if (event.code === 1006) {
        state.connectionError = 'Connection lost unexpectedly';
      } else if (event.code === 1011) {
        state.connectionError = 'Server error occurred';
      } else if (event.code === 1008 || event.code === 1003) {
        state.connectionError = 'Authentication failed';
        return;
      } else {
        state.connectionError = `Connection closed: ${event.reason || 'Unknown reason'}`;
      }
      
      attemptReconnection();
    };
    
    websocket.onerror = (error) => {
      state.connectionError = 'Connection error occurred';
      state.connectionStatus = 'error';
    };
    
  } catch (error) {
    state.connectionError = 'Failed to establish connection';
    state.connectionStatus = 'error';
    attemptReconnection();
  }
}

export function disconnectWebSocket() {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }
  
  stopHeartbeat();
  stopPolling();
  state.isReconnecting = false;
  
  if (websocket) {
    websocket.close(1000, 'User disconnected');
    websocket = null;
  }
  
  state.isConnected = false;
  state.connectionStatus = 'disconnected';
  state.connectionError = null;
  reconnectAttempts = 0;
}

function handleWebSocketMessage(message: WebSocketMessage) {
  switch (message.type) {
    case 'notification':
      if (message.data.action === 'new') {
        const rawNotification = message.data.notification;
        
        // Map the WebSocket notification to RealtimeNotification format
        const notification: RealtimeNotification = {
          ...rawNotification,
          server_id: rawNotification.id, // Map id to server_id
          action: rawNotification.action ? {
            type: rawNotification.action.type,
            target: rawNotification.action.target,
            params: rawNotification.action.params
          } : undefined
        };
        
        state.realtimeNotifications.unshift(notification);
        
        // Check user preference before showing toast
        const userStore = useUserStore();
        const shouldShowToast = userStore.showNotificationToasts;
        
        if (shouldShowToast) {
          addLocalNotification({
            title: notification.title,
            message: notification.message,
            type: notification.type,
            sticky: false,
            duration: 4000
          });
        }
        
      } else if (message.data.action === 'read') {
        const notificationId = message.data.notification.server_id || message.data.notification.id;
        const notification = state.realtimeNotifications.find(n => n.server_id === notificationId);
        if (notification) {
          notification.read = true;
        }
      } else if (message.data.action === 'read_all') {
        // Handle mark all as read
        state.realtimeNotifications.forEach(notification => {
          notification.read = true;
        });
      }
      break;
    case 'notifications_read_all':
      // Handle the notifications_read_all message type
      state.realtimeNotifications.forEach(notification => {
        notification.read = true;
      });
      break;
    case 'heartbeat':
      resetHeartbeatTimeout();
      break;
    case 'heartbeat_response':
      resetHeartbeatTimeout();
      break;
    case 'connection_established':
      resetHeartbeatTimeout();
      break;
    case 'error':
      state.connectionError = message.data.message || 'Server error';
      break;
    default:
      // Silently ignore unknown message types
      break;
  }
}

function attemptReconnection() {
  if (reconnectAttempts >= maxReconnectAttempts) {
    state.connectionError = 'Maximum reconnection attempts reached';
    state.connectionStatus = 'error';
    state.isReconnecting = false;
    
    if (state.isOnline) {
      startPolling();
    }
    return;
  }
  
  if (!state.isOnline) {
    startPolling();
    return;
  }
  
  state.isReconnecting = true;
  state.connectionStatus = 'reconnecting';
  
  const baseDelay = 1000;
  const maxDelay = 30000;
  const delay = Math.min(baseDelay * Math.pow(2, reconnectAttempts), maxDelay);
  const jitter = Math.random() * 1000;
  
  reconnectTimeout = setTimeout(() => {
    reconnectAttempts++;
    connectWebSocket();
  }, delay + jitter);
}

function startHeartbeat() {
  heartbeatInterval = setInterval(() => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'heartbeat',
        timestamp: new Date().toISOString()
      }));
      
      heartbeatTimeout = setTimeout(() => {
        if (websocket) {
          websocket.close();
        }
      }, 10000);
    }
  }, 30000);
}

function stopHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
  }
  
  if (heartbeatTimeout) {
    clearTimeout(heartbeatTimeout);
    heartbeatTimeout = null;
  }
}

function resetHeartbeatTimeout() {
  if (heartbeatTimeout) {
    clearTimeout(heartbeatTimeout);
    heartbeatTimeout = null;
  }
}

function startPolling() {
  if (state.isPolling) return;
  
  state.isPolling = true;
  state.fallbackToPolling = true;
  
  pollingInterval = setInterval(async () => {
    if (!state.isOnline || state.isConnected) {
      stopPolling();
      return;
    }
    
    try {
      await fetchRecentNotifications();
    } catch (error) {
      // Silent error handling
    }
  }, 30000);
  
  fetchRecentNotifications();
}

function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
  
  state.isPolling = false;
  
  if (state.fallbackToPolling) {
    state.fallbackToPolling = false;
  }
}

async function syncMissedNotifications() {
  try {
    const notifications = await fetchRecentNotifications();
    
    const existingIds = new Set(state.realtimeNotifications.map((n: RealtimeNotification) => n.server_id));
    const newNotifications = notifications.filter((n: RealtimeNotification) => !existingIds.has(n.server_id));
    
    if (newNotifications.length > 0) {
      state.realtimeNotifications.unshift(...newNotifications);
    }
  } catch (error) {
    // Silent error handling
  }
}

// API functions
export async function fetchRecentNotifications(): Promise<RealtimeNotification[]> {
  const userStore = useUserStore();
  
  if (!userStore.token) {
    state.connectionError = 'Authentication required';
    return [];
  }

  try {
    const response = await api.get('/notifications?limit=50');
    const notifications = response.data.notifications || [];
    
    // Map API response to RealtimeNotification format
    const mappedNotifications = notifications.map((notification: any) => ({
      ...notification,
      server_id: notification.id.toString(), // Map id to server_id as string
      action: notification.action_type ? {
        type: notification.action_type,
        target: notification.action_target,
        params: notification.action_params
      } : undefined
    }));
    
    state.realtimeNotifications = mappedNotifications;
    
    return mappedNotifications;
  } catch (error: any) {
    if (error.response?.status === 401) {
      state.connectionError = 'Authentication expired';
      return [];
    }
    
    state.connectionError = 'Network error while fetching notifications';
    return [];
  }
}

export async function markAsRead(notificationId: string): Promise<void> {
  const userStore = useUserStore();
  if (!userStore.token) {
    state.connectionError = 'Authentication required';
    return;
  }

  const notification = state.realtimeNotifications.find(n => n.server_id === notificationId);
  const originalReadState = notification?.read;
  if (notification) {
    notification.read = true;
  }

  try {
    // Convert string ID back to integer for API call
    const numericId = parseInt(notificationId, 10);
    if (isNaN(numericId)) {
      throw new Error('Invalid notification ID');
    }
    await api.post(`/notifications/${numericId}/read`);
  } catch (error: any) {
    if (notification && originalReadState !== undefined) {
      notification.read = originalReadState;
    }
    
    if (error.response?.status === 401) {
      state.connectionError = 'Authentication expired';
      return;
    }
  }
}

export async function markAllAsRead(): Promise<void> {
  const userStore = useUserStore();
  if (!userStore.token) {
    state.connectionError = 'Authentication required';
    return;
  }

  const originalStates = state.realtimeNotifications.map(n => ({ id: n.server_id, read: n.read }));
  state.realtimeNotifications.forEach(notification => {
    notification.read = true;
  });

  try {
    await api.post('/notifications/read-all');
  } catch (error: any) {
    originalStates.forEach(({ id, read }) => {
      const notification = state.realtimeNotifications.find(n => n.server_id === id);
      if (notification) {
        notification.read = read;
      }
    });
    
    if (error.response?.status === 401) {
      state.connectionError = 'Authentication expired';
      return;
    }
    
    // Show error toast if user preference allows
    const userStore = useUserStore();
    if (userStore.showNotificationToasts) {
      addLocalNotification({
        title: 'Network Error',
        message: 'Unable to update notification status.',
        type: 'warning',
        sticky: false,
        duration: 3000
      });
    }
  }
}

// Local notification functions
export function addLocalNotification(notification: Omit<Notification, 'id'>) {
  const id = nextId++;
  const newNotification = {
    ...notification,
    id,
    duration: notification.duration ?? 4000,
    sticky: notification.sticky ?? false
  };
  
  state.notifications.push(newNotification);
  return id;
}

export function removeLocalNotification(id: number) {
  const index = state.notifications.findIndex(n => n.id === id);
  if (index !== -1) {
    state.notifications.splice(index, 1);
  }
}

export function executeNotificationAction(notification: RealtimeNotification) {
  if (!notification.action) {
    return;
  }

  const action = notification.action;

  switch (action.type) {
    case 'navigate':
      if (action.target) {
        const target = action.target;
        // Use Vue Router for soft navigation instead of hard reload
        // Import router dynamically to avoid circular dependencies
        import('../router').then(({ default: router }) => {
          // Check if target is an absolute URL or a path
          try {
            const url = new URL(target, window.location.origin);
            const path = url.pathname + url.search + url.hash;
            
            // Add query params if provided
            if (action.params) {
              const query = { ...action.params };
              router.push({ path, query });
            } else {
              router.push(path);
            }
          } catch (e) {
            // If target is already a path (not a full URL), use it directly
            if (action.params) {
              router.push({ path: target, query: action.params });
            } else {
              router.push(target);
            }
          }
        }).catch(err => {
          console.error('Failed to navigate:', err);
          // Fallback to hard navigation if router fails
          window.location.href = target;
        });
      }
      break;

    case 'modal':
      if (action.target) {
        const event = new CustomEvent('open-modal', {
          detail: {
            component: action.target,
            params: action.params || {}
          }
        });
        window.dispatchEvent(event);
      }
      break;

    case 'function':
      if (action.function_name) {
        try {
          const func = (window as any)[action.function_name];
          if (typeof func === 'function') {
            func(action.params || {});
          }
        } catch (error) {
          // Silent error handling
        }
      }
      break;

    default:
      // Silent handling of unknown action types
      break;
  }
}

// Setup online/offline handlers
function setupOnlineOfflineHandlers() {
  const handleOnline = () => {
    state.isOnline = true;
    
    stopPolling();
    
    if (!state.isConnected) {
      connectWebSocket();
    }
    
    // Show connection restored toast if user preference allows
    const userStore = useUserStore();
    if (userStore.showNotificationToasts) {
      addLocalNotification({
        title: 'Connection Restored',
        message: 'Real-time notifications are now available.',
        type: 'success',
        sticky: false,
        duration: 3000
      });
    }
  };

  const handleOffline = () => {
    state.isOnline = false;
    
    if (websocket) {
      websocket.close();
    }
    
    startPolling();
    
    // Show offline toast if user preference allows
    const userStore = useUserStore();
    if (userStore.showNotificationToasts) {
      addLocalNotification({
        title: 'Connection Lost',
        message: 'Working offline. Notifications may be delayed.',
        type: 'warning',
        sticky: true
      });
    }
  };

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
}

// Initialize online/offline handlers
if (typeof window !== 'undefined') {
  setupOnlineOfflineHandlers();
  
  // Subscribe to user store preference changes for real-time updates
  const userStore = useUserStore();
  userStore.onUserDataUpdate((eventType) => {
    if (eventType === 'preferences_updated' || eventType === 'preferences_synced') {
      // The notification store will automatically use the updated preference
      // from the UserStore computed property on the next notification
    }
  });
}

// Export the reactive state and functions
export const notificationStore = {
  state,
  unreadCount,
  connectWebSocket,
  disconnectWebSocket,
  fetchRecentNotifications,
  markAsRead,
  markAllAsRead,
  addLocalNotification,
  removeLocalNotification,
  executeNotificationAction
};
