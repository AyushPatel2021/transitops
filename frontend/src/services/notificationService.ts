import { ref, computed } from 'vue';
import { useAuth } from '../core/useAuth';
import api from '../core/api';

export interface RealtimeNotification {
  id: number;
  server_id: string;
  title: string;
  message: string;
  type: 'success' | 'warning' | 'danger' | 'info';
  sticky: boolean;
  duration?: number;
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
  type: 'notification' | 'notification_read' | 'heartbeat' | 'heartbeat_response' | 'connection_established' | 'error';
  data: any;
  timestamp: string;
}

// Global state for notifications
const realtimeNotifications = ref<RealtimeNotification[]>([]);
const isConnected = ref(false);
const connectionStatus = ref<'connected' | 'connecting' | 'disconnected' | 'error' | 'reconnecting'>('disconnected');
const connectionError = ref<string | null>(null);
const isReconnecting = ref(false);
const isOnline = ref(navigator.onLine);

// WebSocket connection management
let websocket: WebSocket | null = null;
let reconnectAttempts = 0;
let reconnectTimeout: number | null = null;
let heartbeatInterval: number | null = null;
let heartbeatTimeout: number | null = null;

const maxReconnectAttempts = 10;

class NotificationService {
  private static instance: NotificationService;
  private currentUserId: number | null = null;

  static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  private constructor() {
    this.setupOnlineOfflineHandlers();
  }

  // Computed property for unread count
  get unreadCount() {
    return computed(() => {
      return realtimeNotifications.value.filter(n => !n.read).length;
    });
  }

  get notifications() {
    return realtimeNotifications;
  }

  get connectionState() {
    return {
      isConnected,
      connectionStatus,
      connectionError,
      isReconnecting,
      isOnline
    };
  }

  private setupOnlineOfflineHandlers() {
    const handleOnline = () => {
      isOnline.value = true;
      
      if (!isConnected.value && this.currentUserId) {
        this.connectWebSocket();
      }
    };

    const handleOffline = () => {
      isOnline.value = false;
      this.disconnectWebSocket();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
  }

  async initialize(userId: number, token: string) {
    if (this.currentUserId === userId && isConnected.value) {
      return; // Already connected for this user
    }

    this.currentUserId = userId;
    
    // Fetch initial notifications
    await this.fetchRecentNotifications();
    
    // Connect WebSocket
    if (isOnline.value) {
      this.connectWebSocket();
    }
  }

  disconnect() {
    this.currentUserId = null;
    this.disconnectWebSocket();
    realtimeNotifications.value = [];
  }
  private connectWebSocket() {
    if (!this.currentUserId || !isOnline.value) {
      return;
    }

    const { token } = useAuth();
    if (!token.value) {
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

    connectionStatus.value = isReconnecting.value ? 'reconnecting' : 'connecting';
    connectionError.value = null;

    try {
      const getWebSocketUrl = () => {
        const envApiUrl = import.meta.env.VITE_API_URL;
        if (envApiUrl) {
          const wsUrl = envApiUrl.replace(/^https?:/, window.location.protocol === 'https:' ? 'wss:' : 'ws:');
          return `${wsUrl}/ws/notifications`;
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
      
      const wsUrl = `${getWebSocketUrl()}?token=${token.value}`;
      
      websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        isConnected.value = true;
        connectionStatus.value = 'connected';
        connectionError.value = null;
        reconnectAttempts = 0;
        isReconnecting.value = false;
        
        this.startHeartbeat();
        
        if (reconnectAttempts > 0) {
          this.syncMissedNotifications();
        }
      };
      
      websocket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
          this.resetHeartbeatTimeout();
        } catch (error) {
          connectionError.value = 'Message parsing error';
        }
      };
      
      websocket.onclose = (event) => {
        isConnected.value = false;
        connectionStatus.value = 'disconnected';
        websocket = null;
        
        this.stopHeartbeat();
        
        if (event.code === 1000) {
          connectionError.value = null;
          return;
        }
        
        if (event.code === 1006) {
          connectionError.value = 'Connection lost unexpectedly';
        } else if (event.code === 1011) {
          connectionError.value = 'Server error occurred';
        } else if (event.code === 1008 || event.code === 1003) {
          connectionError.value = 'Authentication failed';
          return;
        } else {
          connectionError.value = `Connection closed: ${event.reason || 'Unknown reason'}`;
        }
        
        this.attemptReconnection();
      };
      
      websocket.onerror = (error) => {
        connectionError.value = 'Connection error occurred';
        connectionStatus.value = 'error';
      };
      
    } catch (error) {
      connectionError.value = 'Failed to establish connection';
      connectionStatus.value = 'error';
      this.attemptReconnection();
    }
  }
  private disconnectWebSocket() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    
    this.stopHeartbeat();
    isReconnecting.value = false;
    
    if (websocket) {
      websocket.close(1000, 'User disconnected');
      websocket = null;
    }
    
    isConnected.value = false;
    connectionStatus.value = 'disconnected';
    connectionError.value = null;
    reconnectAttempts = 0;
  }

  private attemptReconnection() {
    if (reconnectAttempts >= maxReconnectAttempts) {
      connectionError.value = 'Maximum reconnection attempts reached';
      connectionStatus.value = 'error';
      isReconnecting.value = false;
      return;
    }
    
    if (!isOnline.value) {
      return;
    }
    
    isReconnecting.value = true;
    connectionStatus.value = 'reconnecting';
    
    const baseDelay = 1000;
    const maxDelay = 30000;
    const delay = Math.min(baseDelay * Math.pow(2, reconnectAttempts), maxDelay);
    const jitter = Math.random() * 1000;
    
    reconnectTimeout = setTimeout(() => {
      reconnectAttempts++;
      this.connectWebSocket();
    }, delay + jitter);
  }

  private startHeartbeat() {
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

  private stopHeartbeat() {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
    
    if (heartbeatTimeout) {
      clearTimeout(heartbeatTimeout);
      heartbeatTimeout = null;
    }
  }

  private resetHeartbeatTimeout() {
    if (heartbeatTimeout) {
      clearTimeout(heartbeatTimeout);
      heartbeatTimeout = null;
    }
  }

  private handleWebSocketMessage(message: WebSocketMessage) {
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
          
          realtimeNotifications.value.unshift(notification);
        } else if (message.data.action === 'read') {
          const notificationId = message.data.notification.server_id || message.data.notification.id;
          const notification = realtimeNotifications.value.find(n => n.server_id === notificationId);
          if (notification) {
            notification.read = true;
          }
        }
        break;
      case 'heartbeat':
        this.resetHeartbeatTimeout();
        break;
      case 'connection_established':
        // Handle connection established message from server
        this.resetHeartbeatTimeout();
        break;
      case 'heartbeat_response':
        // Handle heartbeat response from server
        this.resetHeartbeatTimeout();
        break;
      default:
        // Silent handling of unknown message types
        break;
    }
  }

  private async syncMissedNotifications() {
    try {
      const notifications = await this.fetchRecentNotifications();
      
      const existingIds = new Set(realtimeNotifications.value.map(n => n.server_id));
      const newNotifications = notifications.filter(n => !existingIds.has(n.server_id));
      
      if (newNotifications.length > 0) {
        realtimeNotifications.value.unshift(...newNotifications);
      }
    } catch (error) {
      // Silent error handling
    }
  }

  async fetchRecentNotifications(): Promise<RealtimeNotification[]> {
    const { token } = useAuth();
    if (!token.value) {
      connectionError.value = 'Authentication required';
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
      
      realtimeNotifications.value = mappedNotifications;
      return mappedNotifications;
    } catch (error: any) {
      if (error.response?.status === 401) {
        connectionError.value = 'Authentication expired';
        return [];
      }
      
      connectionError.value = 'Network error while fetching notifications';
      return [];
    }
  }

  async markAsRead(notificationId: string): Promise<void> {
    const { token } = useAuth();
    if (!token.value) {
      connectionError.value = 'Authentication required';
      return;
    }

    const notification = realtimeNotifications.value.find(n => n.server_id === notificationId);
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
        connectionError.value = 'Authentication expired';
        return;
      }
    }
  }

  async markAllAsRead(): Promise<void> {
    const { token } = useAuth();
    if (!token.value) {
      connectionError.value = 'Authentication required';
      return;
    }

    const originalStates = realtimeNotifications.value.map(n => ({ id: n.server_id, read: n.read }));
    realtimeNotifications.value.forEach(notification => {
      notification.read = true;
    });

    try {
      await api.post('/notifications/read-all');
    } catch (error: any) {
      originalStates.forEach(({ id, read }) => {
        const notification = realtimeNotifications.value.find(n => n.server_id === id);
        if (notification) {
          notification.read = read;
        }
      });
      
      // Silent error handling
    }
  }

  executeNotificationAction(notification: RealtimeNotification) {
    if (!notification.action) {
      return;
    }

    const action = notification.action;

    switch (action.type) {
      case 'navigate':
        if (action.target) {
          const target = action.target;
          // Use Vue Router for soft navigation instead of hard reload
          import('../router').then(({ default: router }) => {
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
}

// Export singleton instance
export const notificationService = NotificationService.getInstance();

// Export composable for components
export function useNotificationService() {
  return {
    notifications: notificationService.notifications,
    unreadCount: notificationService.unreadCount,
    connectionState: notificationService.connectionState,
    markAsRead: notificationService.markAsRead.bind(notificationService),
    markAllAsRead: notificationService.markAllAsRead.bind(notificationService),
    fetchRecentNotifications: notificationService.fetchRecentNotifications.bind(notificationService),
    executeNotificationAction: notificationService.executeNotificationAction.bind(notificationService)
  };
}
