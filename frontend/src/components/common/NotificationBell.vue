<template>
  <div class="notification-bell" ref="bellRef">
    <!-- Bell Icon Button -->
    <button 
      class="bell-button"
      @click="toggleDropdown"
      @touchstart="handleTouchStart"
      @touchend="handleTouchEnd"
      @keydown="handleBellKeydown"
      :class="{ 'has-notifications': unreadCount > 0, 'active': isDropdownOpen, 'touch-active': isTouchActive, 'ringing': isRinging }"
      :aria-label="unreadCount > 0 ? `${unreadCount} unread notifications` : 'Notifications'"
      :aria-expanded="isDropdownOpen"
      :aria-haspopup="true"
      :aria-describedby="unreadCount > 0 ? 'notification-count' : undefined"
      type="button"
    >
      <!-- Bell Icon SVG -->
      <div class="bell-icon-container" :class="{ 'ringing': isRinging }">
        <svg 
          class="bell-icon" 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <!-- Bell body -->
          <path 
            d="M12 2C13.1 2 14 2.9 14 4C16.3 4.89 18 7.22 18 10V16L20 18V19H4V18L6 16V10C6 7.22 7.7 4.89 10 4C10 2.9 10.9 2 12 2Z" 
            :fill="bellFillColor"
            :stroke="bellStrokeColor"
            stroke-width="1.5"
          />
          <!-- Bell clapper -->
          <circle 
            cx="12" 
            cy="21" 
            r="1.5" 
            :fill="bellStrokeColor"
          />
        </svg>
        
        <!-- Ring animation lines -->
        <div v-if="isRinging" class="ring-lines">
          <svg class="ring-line ring-line-left" width="24" height="24" viewBox="0 0 24 24">
            <path d="M8 6C8 6 6 8 6 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
            <path d="M5 4C5 4 2 7 2 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
          </svg>
          <svg class="ring-line ring-line-right" width="24" height="24" viewBox="0 0 24 24">
            <path d="M16 6C16 6 18 8 18 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
            <path d="M19 4C19 4 22 7 22 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
          </svg>
        </div>
      </div>
      
      <!-- Notification count badge -->
      <span 
        v-if="unreadCount > 0" 
        class="unread-badge"
        :id="'notification-count'"
        :aria-label="`${unreadCount} unread`"
        role="status"
        aria-live="polite"
      >
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <!-- Dropdown Panel -->
    <Transition name="dropdown">
      <div 
        v-if="isDropdownOpen" 
        class="notification-dropdown" 
        @click.stop 
        @touchstart.stop
        @keydown="handleDropdownKeydown"
        role="dialog"
        aria-modal="false"
        aria-labelledby="notifications-title"
        aria-describedby="notifications-description"
        tabindex="-1"
        ref="dropdownRef"
      >
        <div class="dropdown-header">
          <h3 id="notifications-title">Notifications</h3>
          <div class="header-actions">
            <!-- Connection Status Indicator -->
            <div 
              class="connection-status" 
              :class="connectionStatusClass" 
              :title="connectionStatusText"
              :aria-label="connectionStatusText"
              role="status"
              aria-live="polite"
            >
              <i :class="connectionStatusIcon" aria-hidden="true"></i>
            </div>
            <button 
              v-if="unreadCount > 0" 
              class="mark-all-read-btn"
              @click="handleMarkAllAsRead"
              @touchstart="handleButtonTouchStart"
              @touchend="handleButtonTouchEnd"
              :disabled="isMarkingAllRead"
              :aria-label="isMarkingAllRead ? 'Marking all notifications as read' : 'Mark all notifications as read'"
              type="button"
            >
              {{ isMarkingAllRead ? 'Marking...' : 'Mark all read' }}
            </button>
          </div>
        </div>

        <div class="dropdown-content" role="region" aria-label="Notifications list">
          <!-- Screen reader description -->
          <div id="notifications-description" class="sr-only">
            {{ displayNotifications.length === 0 ? 'No notifications available' : `${displayNotifications.length} notifications available. Use arrow keys to navigate.` }}
          </div>

          <!-- Connection Issue Warning -->
          <div v-if="!isConnected && !fallbackToPolling" class="connection-warning" role="alert" aria-live="assertive">
            <div class="warning-content">
              <i class="icofont-warning" aria-hidden="true"></i>
              <div class="warning-text">
                <p><strong>Connection Issue</strong></p>
                <p>{{ connectionStatusText }}</p>
              </div>
            </div>
          </div>

          <!-- Fallback Mode Notice -->
          <div v-if="fallbackToPolling" class="fallback-notice" role="status" aria-live="polite">
            <div class="notice-content">
              <i class="icofont-clock-time" aria-hidden="true"></i>
              <div class="notice-text">
                <p><strong>Backup Mode</strong></p>
                <p>Using periodic updates. Some features may be limited.</p>
              </div>
            </div>
          </div>
          
          <div v-if="isLoading" class="loading-state" role="status" aria-live="polite" aria-label="Loading notifications">
            <div class="loading-spinner" aria-hidden="true"></div>
            <span>Loading notifications...</span>
          </div>

          <!-- Empty State -->
          <div v-else-if="displayNotifications.length === 0" class="empty-state" role="status">
            <i class="icofont-notification empty-icon" aria-hidden="true"></i>
            <p>No notifications yet</p>
          </div>

          <!-- Notifications List -->
          <div v-else class="notifications-list" role="list" aria-label="Notifications">
            <div 
              v-for="(notification, index) in displayNotifications" 
              :key="notification.server_id"
              class="notification-item"
              :class="{ 'unread': !notification.read, 'touch-active': touchActiveNotification === notification.server_id, 'focused': focusedNotificationIndex === index }"
              :data-notification-index="index"
              :data-notification-id="notification.server_id"
              @click="handleNotificationClick(notification)"
              @touchstart="handleNotificationTouchStart(notification)"
              @touchend="handleNotificationTouchEnd"
              @keydown="handleNotificationKeydown($event, notification, index)"
              role="listitem"
              :tabindex="focusedNotificationIndex === index ? 0 : -1"
              :aria-label="`${notification.read ? 'Read' : 'Unread'} notification: ${notification.title}. ${notification.message}. ${formatTime(notification.created_at)}. Press Enter to open.`"
              :aria-describedby="`notification-${notification.server_id}-details`"
            >
              <div class="notification-content">
                <div class="notification-icon" :class="`type-${notification.type}`" aria-hidden="true">
                  <i :class="getNotificationIcon(notification.type)"></i>
                </div>
                <div class="notification-text">
                  <h4 class="notification-title">{{ notification.title }}</h4>
                  <p class="notification-message">{{ notification.message }}</p>
                  <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
                </div>
                <div v-if="!notification.read" class="unread-indicator" aria-hidden="true"></div>
                <!-- Hidden details for screen readers -->
                <div :id="`notification-${notification.server_id}-details`" class="sr-only">
                  Type: {{ notification.type }}. Status: {{ notification.read ? 'Read' : 'Unread' }}.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Backdrop -->
    <div 
      v-if="isDropdownOpen" 
      class="dropdown-backdrop" 
      @click="closeDropdown"
    ></div>
  </div>
</template>

<script setup lang="ts">
// Import the watch function
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useNotificationsStore } from '../../composables/useNotificationsStore';
import type { RealtimeNotification } from '../../stores/notificationStore';
import { useAuth } from '../../core/useAuth';

interface Props {
  maxVisible?: number;
  position?: 'left' | 'right';
}

const props = withDefaults(defineProps<Props>(), {
  maxVisible: 10,
  position: 'right'
});

const { 
  realtimeNotifications, 
  unreadCount, 
  isConnected,
  connectionStatus,
  connectionError,
  isOnline,
  fallbackToPolling,
  fetchRecentNotifications,
  markAsRead,
  markAllAsRead,
  executeNotificationAction
} = useNotificationsStore();

const { user } = useAuth();

// Component state
const isDropdownOpen = ref(false);
const isLoading = ref(false);
const isMarkingAllRead = ref(false);
const bellRef = ref<HTMLElement>();
const dropdownRef = ref<HTMLElement>();
const isTouchActive = ref(false);
const touchActiveNotification = ref<string | null>(null);
const focusedNotificationIndex = ref(-1);
const isRinging = ref(false); // New state for ring animation
let touchStartTime = 0;

// Computed properties
const displayNotifications = computed(() => {
  return realtimeNotifications.value.slice(0, props.maxVisible);
});

const connectionStatusText = computed(() => {
  if (!isOnline.value) {
    return 'Offline - Limited functionality';
  }
  
  switch (connectionStatus.value) {
    case 'connected':
      return 'Connected - Real-time updates active';
    case 'connecting':
      return 'Connecting...';
    case 'reconnecting':
      return 'Reconnecting...';
    case 'error':
      return connectionError.value || 'Connection error';
    case 'disconnected':
      if (fallbackToPolling.value) {
        return 'Using backup connection';
      }
      return 'Disconnected';
    default:
      return 'Unknown status';
  }
});

const connectionStatusIcon = computed(() => {
  if (!isOnline.value) {
    return 'icofont-wifi-off';
  }
  
  switch (connectionStatus.value) {
    case 'connected':
      return 'icofont-wifi';
    case 'connecting':
    case 'reconnecting':
      return 'icofont-refresh';
    case 'error':
      return 'icofont-warning';
    case 'disconnected':
      if (fallbackToPolling.value) {
        return 'icofont-clock-time';
      }
      return 'icofont-wifi-off';
    default:
      return 'icofont-question-circle';
  }
});

const connectionStatusClass = computed(() => {
  if (!isOnline.value) {
    return 'status-offline';
  }
  
  switch (connectionStatus.value) {
    case 'connected':
      return 'status-connected';
    case 'connecting':
    case 'reconnecting':
      return 'status-connecting';
    case 'error':
      return 'status-error';
    case 'disconnected':
      if (fallbackToPolling.value) {
        return 'status-fallback';
      }
      return 'status-disconnected';
    default:
      return 'status-unknown';
  }
});

// Bell icon colors based on state
const bellFillColor = computed(() => {
  if (unreadCount.value > 0) {
    return 'currentColor'; // Will use the CSS color
  }
  return 'none'; // Outline only when no notifications
});

const bellStrokeColor = computed(() => {
  return 'currentColor'; // Always use current CSS color
});

// Methods
// Methods
const triggerRingAnimation = () => {
  isRinging.value = true;
  setTimeout(() => {
    isRinging.value = false;
  }, 1000); // Ring for 1 second
};

// Watch for new notifications to trigger ring animation
watch(unreadCount, (newCount, oldCount) => {
  // Only ring if count increased (new notification arrived)
  if (newCount > oldCount && oldCount !== undefined) {
    triggerRingAnimation();
  }
});

const toggleDropdown = async () => {
  if (!isDropdownOpen.value) {
    isDropdownOpen.value = true;
    await loadNotifications();
    // Focus management for accessibility
    await nextTick();
    if (dropdownRef.value) {
      dropdownRef.value.focus();
      // Start with no notification focused initially
      focusedNotificationIndex.value = -1;
    }
  } else {
    closeDropdown();
  }
};

const closeDropdown = () => {
  isDropdownOpen.value = false;
  focusedNotificationIndex.value = -1;
  
  // Only return focus to bell button if no other element is being focused
  // This prevents stealing focus from form fields and other interactive elements
  setTimeout(() => {
    const activeEl = document.activeElement;
    
    // Don't steal focus if user is interacting with form elements
    if (activeEl && (
      activeEl.tagName === 'INPUT' ||
      activeEl.tagName === 'TEXTAREA' ||
      activeEl.tagName === 'SELECT' ||
      activeEl.tagName === 'BUTTON' ||
      activeEl.closest('input') ||
      activeEl.closest('textarea') ||
      activeEl.closest('select') ||
      activeEl.closest('.many2one-container') ||
      activeEl.closest('.field-wrapper') ||
      activeEl.closest('.base-form-pivot')
    )) {
      // Don't return focus to bell if user is working with form elements
      return;
    }
    
    // Only return focus if no meaningful element has focus
    if (activeEl === document.body || activeEl === null || activeEl === document.documentElement) {
      if (bellRef.value) {
        const button = bellRef.value.querySelector('.bell-button') as HTMLElement;
        if (button) {
          button.focus();
        }
      }
    }
  }, 0);
};

const loadNotifications = async () => {
  if (isLoading.value) return;
  
  // Only fetch if we don't have notifications or if there was a connection issue
  if (realtimeNotifications.value.length === 0 || !isConnected.value) {
    isLoading.value = true;
    try {
      await fetchRecentNotifications();
    } catch (error) {
      // Silent error handling
    } finally {
      isLoading.value = false;
    }
  }
};

const handleNotificationClick = async (notification: RealtimeNotification) => {
  // Mark as read if not already read
  if (!notification.read) {
    await markAsRead(notification.server_id);
  }

  // Execute the notification action
  executeNotificationAction(notification);

  // Close dropdown after action
  closeDropdown();
};

const handleMarkAllAsRead = async () => {
  if (isMarkingAllRead.value) return;
  
  isMarkingAllRead.value = true;
  try {
    await markAllAsRead();
  } catch (error) {
    // Silent error handling
  } finally {
    isMarkingAllRead.value = false;
  }
};

const handleViewMore = () => {
  // Navigate to a full notifications page or expand the dropdown
  // For now, we'll just close the dropdown
  closeDropdown();
  // TODO: Implement navigation to full notifications page
};

const getNotificationIcon = (type: string): string => {
  switch (type) {
    case 'success':
      return 'icofont-check-circled';
    case 'warning':
      return 'icofont-warning';
    case 'danger':
      return 'icofont-error';
    default:
      return 'icofont-info-circle';
  }
};

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

  if (diffInMinutes < 1) {
    return 'Just now';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  } else if (diffInMinutes < 1440) {
    const hours = Math.floor(diffInMinutes / 60);
    return `${hours}h ago`;
  } else {
    const days = Math.floor(diffInMinutes / 1440);
    return `${days}d ago`;
  }
};

// Touch handling methods for better mobile experience
const handleTouchStart = () => {
  isTouchActive.value = true;
  touchStartTime = Date.now();
};

const handleTouchEnd = () => {
  // Add a small delay to show the touch feedback
  setTimeout(() => {
    isTouchActive.value = false;
  }, 150);
};

const handleNotificationTouchStart = (notification: RealtimeNotification) => {
  touchActiveNotification.value = notification.server_id;
  touchStartTime = Date.now();
};

const handleNotificationTouchEnd = () => {
  // Add a small delay to show the touch feedback
  setTimeout(() => {
    touchActiveNotification.value = null;
  }, 150);
};

const handleButtonTouchStart = () => {
  // Generic touch start handler for buttons
  touchStartTime = Date.now();
};

const handleButtonTouchEnd = () => {
  // Generic touch end handler for buttons
  // Could add haptic feedback here if supported
};

// Keyboard navigation handlers
const handleBellKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Enter':
    case ' ': // Space key
      event.preventDefault();
      toggleDropdown();
      break;
    case 'Escape':
      if (isDropdownOpen.value) {
        event.preventDefault();
        closeDropdown();
      }
      break;
  }
};

const handleDropdownKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Escape':
      event.preventDefault();
      closeDropdown();
      break;
    case 'ArrowDown':
      event.preventDefault();
      navigateNotifications('down');
      break;
    case 'ArrowUp':
      event.preventDefault();
      navigateNotifications('up');
      break;
    case 'Home':
      event.preventDefault();
      focusFirstNotification();
      break;
    case 'End':
      event.preventDefault();
      focusLastNotification();
      break;
    case 'Tab':
      // Allow normal tab behavior but manage focus
      handleTabNavigation(event);
      break;
  }
};

const handleNotificationKeydown = (event: KeyboardEvent, notification: RealtimeNotification, index: number) => {
  switch (event.key) {
    case 'Enter':
    case ' ': // Space key
      event.preventDefault();
      event.stopPropagation(); // Prevent bubbling
      handleNotificationClick(notification);
      break;
    case 'ArrowDown':
      // Don't handle arrow keys here - let the dropdown handle them
      // This prevents double navigation
      break;
    case 'ArrowUp':
      // Don't handle arrow keys here - let the dropdown handle them
      // This prevents double navigation
      break;
    case 'Home':
      event.preventDefault();
      event.stopPropagation(); // Prevent bubbling
      focusFirstNotification();
      break;
    case 'End':
      event.preventDefault();
      event.stopPropagation(); // Prevent bubbling
      focusLastNotification();
      break;
    case 'Escape':
      event.preventDefault();
      event.stopPropagation(); // Prevent bubbling
      closeDropdown();
      break;
  }
};

const handleViewMoreKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Enter':
    case ' ': // Space key
      event.preventDefault();
      handleViewMore();
      break;
    case 'Escape':
      event.preventDefault();
      closeDropdown();
      break;
  }
};

// Navigation helpers
const navigateNotifications = (direction: 'up' | 'down') => {
  const notifications = displayNotifications.value;
  
  if (notifications.length === 0) {
    return;
  }

  const currentIndex = focusedNotificationIndex.value;
  let newIndex = currentIndex;
  
  if (direction === 'down') {
    // If no notification is focused, start with the first one
    if (newIndex === -1) {
      newIndex = 0;
    } else {
      const nextIndex = newIndex < notifications.length - 1 ? newIndex + 1 : newIndex;
      newIndex = nextIndex;
    }
  } else {
    // If no notification is focused, start with the last one
    if (newIndex === -1) {
      newIndex = notifications.length - 1;
    } else {
      const nextIndex = newIndex > 0 ? newIndex - 1 : newIndex;
      newIndex = nextIndex;
    }
  }
  
  if (newIndex !== currentIndex) {
    focusedNotificationIndex.value = newIndex;
    focusNotificationAtIndex(newIndex);
  }
};

const focusFirstNotification = () => {
  if (displayNotifications.value.length > 0) {
    focusedNotificationIndex.value = 0;
    focusNotificationAtIndex(0);
  }
};

const focusLastNotification = () => {
  const lastIndex = displayNotifications.value.length - 1;
  if (lastIndex >= 0) {
    focusedNotificationIndex.value = lastIndex;
    focusNotificationAtIndex(lastIndex);
  }
};

const focusNotificationAtIndex = (index: number) => {
  nextTick(() => {
    if (!dropdownRef.value) return;
    
    // Use data attribute for more reliable selection
    const targetElement = dropdownRef.value.querySelector(`[data-notification-index="${index}"]`) as HTMLElement;
    
    if (targetElement) {
      targetElement.focus();
      
      // Scroll into view
      targetElement.scrollIntoView({ 
        block: 'nearest', 
        behavior: 'smooth' 
      });
    }
  });
};

const handleTabNavigation = (event: KeyboardEvent) => {
  // Get all focusable elements within the dropdown
  const focusableElements = dropdownRef.value?.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  if (!focusableElements || focusableElements.length === 0) return;
  
  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
  
  if (event.shiftKey) {
    // Shift + Tab (backward)
    if (document.activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
    }
  } else {
    // Tab (forward)
    if (document.activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  }
};

// Handle clicks outside the component
const handleClickOutside = (event: Event) => {
  // Only close dropdown if it's actually open and the click is truly outside
  if (!isDropdownOpen.value) return;
  
  if (bellRef.value && !bellRef.value.contains(event.target as Node)) {
    // Don't close if clicking on form elements or other interactive elements
    const target = event.target as HTMLElement;
    if (target && (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'SELECT' ||
      target.tagName === 'BUTTON' ||
      target.closest('input') ||
      target.closest('textarea') ||
      target.closest('select') ||
      target.closest('button') ||
      target.closest('.many2one-container') ||
      target.closest('.field-wrapper')
    )) {
      // Don't close dropdown when clicking on form elements
      return;
    }
    
    closeDropdown();
  }
};

// Lifecycle hooks
onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  
  // Note: WebSocket connection is now handled by the notification manager
  // which is initialized by the UserStore after login. We don't need to
  // initialize it again here to avoid duplicate connections.
  
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

// Screen reader only content
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.notification-bell {
  position: relative;
  display: inline-block;
}

.bell-button {
  position: relative;
  background: transparent;
  border: none;
  padding: 0.75rem; // Increased padding for better touch target
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: v.$text-secondary;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 44px; // Minimum touch target size
  min-height: 44px; // Minimum touch target size
  -webkit-tap-highlight-color: transparent; // Remove default tap highlight

  // Focus styles for accessibility
  &:focus {
    outline: 2px solid v.$primary-color;
    outline-offset: 2px;
  }

  &:focus:not(:focus-visible) {
    outline: none;
  }

  &:focus-visible {
    outline: 2px solid v.$primary-color;
    outline-offset: 2px;
  }

  &:hover {
    background: v.$border-light;
    color: v.$text-primary;
  }

  &:active,
  &.touch-active {
    background: v.$primary-color;
    color: v.$white;
    transform: scale(0.95);
  }

  &.active {
    background: v.$primary-color;
    color: v.$white;
    
    .bell-icon {
      color: v.$white;
    }
  }

  &.has-notifications {
    color: v.$primary-color;
    
    .bell-icon {
      color: v.$primary-color;
    }
    
    &.active {
      .bell-icon {
        color: v.$white;
      }
    }
  }

  &.ringing {
    .bell-icon-container {
      animation: bell-shake 0.8s ease-in-out;
    }
    
    .bell-icon {
      color: v.$primary-color;
    }
    
    .ring-lines {
      animation: ring-fade 1s ease-out;
    }
  }

  .bell-icon-container {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .bell-icon {
    transition: color 0.2s ease;
    color: v.$text-secondary;
    
    @media (max-width: 768px) {
      width: 22px;
      height: 22px;
    }
  }

  .ring-lines {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    pointer-events: none;
    color: v.$primary-color;
    opacity: 0.7;
  }

  .ring-line {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    
    &.ring-line-left {
      transform: translate(-50%, -50%) translateX(-12px);
      animation: ring-pulse-left 1s ease-out;
    }
    
    &.ring-line-right {
      transform: translate(-50%, -50%) translateX(12px);
      animation: ring-pulse-right 1s ease-out;
    }
  }

  .unread-badge {
    position: absolute;
    top: 4px;
    right: 4px;
    background: v.$danger-color;
    color: v.$white;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.15rem 0.35rem;
    border-radius: 12px;
    min-width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
    
    @media (max-width: 768px) {
      font-size: 0.75rem;
      min-width: 22px;
      height: 22px;
      top: 2px;
      right: 2px;
    }
  }
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 380px;
  max-height: 500px;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 12px;
  box-shadow: 0 10px 25px v.$shadow-medium;
  z-index: 1000;
  overflow: hidden;

  // Focus styles for accessibility
  &:focus {
    outline: 2px solid v.$primary-color;
    outline-offset: -2px;
  }

  &:focus:not(:focus-visible) {
    outline: none;
  }

  &:focus-visible {
    outline: 2px solid v.$primary-color;
    outline-offset: -2px;
  }

  // Enhanced mobile responsiveness
  @media (max-width: 768px) {
    width: calc(100vw - 2rem);
    max-width: 380px;
    right: -1rem;
    max-height: 70vh; // Limit height on mobile
    border-radius: 16px; // Larger border radius on mobile
  }

  @media (max-width: 480px) {
    width: calc(100vw - 1rem);
    right: -0.5rem;
    max-height: 75vh;
    top: calc(100% + 12px); // More space on small screens
  }

  // For very small screens, make it nearly full width
  @media (max-width: 360px) {
    width: calc(100vw - 0.5rem);
    right: -0.25rem;
  }
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid v.$border-color;
  background: v.$bg-main;

  h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: v.$text-primary;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .connection-status {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    font-size: 12px;
    
    &.status-connected {
      background: rgba(v.$success-color, 0.1);
      color: v.$success-color;
    }
    
    &.status-connecting {
      background: rgba(v.$info-color, 0.1);
      color: v.$info-color;
      
      i {
        animation: spin 1s linear infinite;
      }
    }
    
    &.status-error,
    &.status-disconnected {
      background: rgba(v.$danger-color, 0.1);
      color: v.$danger-color;
    }
    
    &.status-fallback {
      background: rgba(v.$warning-color, 0.1);
      color: v.$warning-color;
    }
    
    &.status-offline {
      background: rgba(v.$text-secondary, 0.1);
      color: v.$text-secondary;
    }
  }

  .mark-all-read-btn {
    background: transparent;
    border: none;
    color: v.$primary-color;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    padding: 0.5rem 0.75rem; // Increased padding for better touch target
    border-radius: 6px;
    transition: all 0.2s ease;
    min-height: 36px; // Minimum touch target
    -webkit-tap-highlight-color: transparent;

    // Focus styles for accessibility
    &:focus {
      outline: 2px solid v.$primary-color;
      outline-offset: 2px;
    }

    &:focus:not(:focus-visible) {
      outline: none;
    }

    &:focus-visible {
      outline: 2px solid v.$primary-color;
      outline-offset: 2px;
    }

    &:hover {
      background: rgba(v.$primary-color, 0.1);
    }

    &:active {
      background: rgba(v.$primary-color, 0.2);
      transform: scale(0.95);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    @media (max-width: 768px) {
      font-size: 0.9rem;
      padding: 0.6rem 0.8rem;
    }
  }
}

.dropdown-content {
  max-height: 400px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch; // Smooth scrolling on iOS
  
  @media (max-width: 768px) {
    max-height: calc(70vh - 120px); // Account for header and footer
  }
  
  @media (max-width: 480px) {
    max-height: calc(75vh - 120px);
  }
}

.connection-warning,
.fallback-notice {
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid v.$border-light;
  
  .warning-content,
  .notice-content {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  i {
    font-size: 16px;
    margin-top: 0.125rem;
  }
  
  .warning-text,
  .notice-text {
    flex: 1;
    
    p {
      margin: 0;
      font-size: 0.8rem;
      line-height: 1.3;
      
      &:first-child {
        font-weight: 600;
        margin-bottom: 0.25rem;
      }
    }
  }
}

.connection-warning {
  background: rgba(v.$danger-color, 0.02);
  
  i {
    color: v.$danger-color;
  }
  
  .warning-text p:first-child {
    color: v.$danger-color;
  }
  
  .warning-text p:last-child {
    color: v.$text-secondary;
  }
}

.fallback-notice {
  background: rgba(v.$warning-color, 0.02);
  
  i {
    color: v.$warning-color;
  }
  
  .notice-text p:first-child {
    color: v.$warning-color;
  }
  
  .notice-text p:last-child {
    color: v.$text-secondary;
  }
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: v.$text-secondary;
  gap: 0.75rem;

  .loading-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid v.$border-color;
    border-top: 2px solid v.$primary-color;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  color: v.$text-secondary;

  .empty-icon {
    font-size: 48px;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  p {
    margin: 0;
    font-size: 0.9rem;
  }
}

.notifications-list {
  .notification-item {
    cursor: pointer;
    transition: all 0.2s ease;
    -webkit-tap-highlight-color: transparent;
    min-height: 60px; // Minimum touch target height

    // Focus styles for accessibility
    &:focus {
      outline: 2px solid v.$primary-color;
      outline-offset: -2px;
      background: rgba(v.$primary-color, 0.05);
    }

    &:focus:not(:focus-visible) {
      outline: none;
    }

    &:focus-visible {
      outline: 2px solid v.$primary-color;
      outline-offset: -2px;
      background: rgba(v.$primary-color, 0.05);
    }

    &.focused {
      background: rgba(v.$primary-color, 0.05);
      border-left: 3px solid v.$primary-color;
    }

    &:hover {
      background: v.$bg-main;
    }

    &:active,
    &.touch-active {
      background: rgba(v.$primary-color, 0.05);
      transform: scale(0.98);
    }

    &.unread {
      background: rgba(v.$primary-color, 0.02);
      border-left: 3px solid v.$primary-color;
      
      &:active,
      &.touch-active {
        background: rgba(v.$primary-color, 0.08);
      }

      &.focused {
        background: rgba(v.$primary-color, 0.08);
      }
    }

    // Ensure read notifications don't have the blue border
    &:not(.unread) {
      border-left: 3px solid transparent;
      
      &.focused {
        background: rgba(v.$primary-color, 0.05);
        border-left: 3px solid v.$primary-color;
      }
    }

    &:not(:last-child) {
      border-bottom: 1px solid v.$border-light;
    }
  }
}

.notification-content {
  display: flex;
  align-items: flex-start;
  padding: 1rem 1.25rem;
  gap: 0.75rem;
  position: relative;
  
  @media (max-width: 768px) {
    padding: 1.25rem 1rem; // Slightly more vertical padding on mobile
    gap: 1rem;
  }
  
  @media (max-width: 480px) {
    padding: 1rem 0.75rem;
  }
}

.notification-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;

  .icon {
    font-size: 16px;
  }

  @media (max-width: 768px) {
    width: 36px;
    height: 36px;
    
    .icon {
      font-size: 18px;
    }
  }

  &.type-success {
    background: rgba(v.$success-color, 0.1);
    color: v.$success-color;
  }

  &.type-warning {
    background: rgba(v.$warning-color, 0.1);
    color: v.$warning-color;
  }

  &.type-danger {
    background: rgba(v.$danger-color, 0.1);
    color: v.$danger-color;
  }

  &.type-info {
    background: rgba(v.$info-color, 0.1);
    color: v.$info-color;
  }
}

.notification-text {
  flex: 1;
  min-width: 0;

  .notification-title {
    margin: 0 0 0.25rem 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: v.$text-primary;
    line-height: 1.3;
    
    @media (max-width: 768px) {
      font-size: 0.95rem;
      line-height: 1.4;
    }
  }

  .notification-message {
    margin: 0 0 0.5rem 0;
    font-size: 0.85rem;
    color: v.$text-secondary;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    
    @media (max-width: 768px) {
      font-size: 0.9rem;
      line-height: 1.5;
      -webkit-line-clamp: 3; // Allow more lines on mobile
    }
  }

  .notification-time {
    font-size: 0.75rem;
    color: v.$text-placeholder;
    
    @media (max-width: 768px) {
      font-size: 0.8rem;
    }
  }
}

.unread-indicator {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  width: 8px;
  height: 8px;
  background: v.$primary-color;
  border-radius: 50%;
}

.dropdown-footer {
  padding: 0.75rem 1.25rem;
  border-top: 1px solid v.$border-color;
  background: v.$bg-main;

  .view-more-btn {
    width: 100%;
    background: transparent;
    border: 1px solid v.$border-color;
    color: v.$text-secondary;
    padding: 0.75rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s ease;
    min-height: 44px; // Minimum touch target
    -webkit-tap-highlight-color: transparent;

    // Focus styles for accessibility
    &:focus {
      outline: 2px solid v.$primary-color;
      outline-offset: 2px;
    }

    &:focus:not(:focus-visible) {
      outline: none;
    }

    &:focus-visible {
      outline: 2px solid v.$primary-color;
      outline-offset: 2px;
    }

    &:hover {
      background: v.$border-light;
      color: v.$text-primary;
    }

    &:active {
      background: rgba(v.$primary-color, 0.1);
      transform: scale(0.98);
    }
    
    @media (max-width: 768px) {
      font-size: 0.9rem;
      padding: 0.875rem;
      border-radius: 10px;
    }
  }
}

.dropdown-backdrop {
  position: fixed;
  inset: 0;
  z-index: 999;
}

// Animations
@keyframes bell-shake {
  0%, 100% { 
    transform: rotate(0deg); 
  }
  10%, 30%, 50%, 70%, 90% { 
    transform: rotate(-8deg); 
  }
  20%, 40%, 60%, 80% { 
    transform: rotate(8deg); 
  }
}

@keyframes ring-fade {
  0% {
    opacity: 0;
    transform: scale(0.8);
  }
  50% {
    opacity: 0.8;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(1.2);
  }
}

@keyframes ring-pulse-left {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) translateX(-8px) scale(0.8);
  }
  50% {
    opacity: 0.8;
    transform: translate(-50%, -50%) translateX(-12px) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) translateX(-16px) scale(1.1);
  }
}

@keyframes ring-pulse-right {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) translateX(8px) scale(0.8);
  }
  50% {
    opacity: 0.8;
    transform: translate(-50%, -50%) translateX(12px) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) translateX(16px) scale(1.1);
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

// Dropdown transition
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
  transform-origin: top right;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

.dropdown-enter-to,
.dropdown-leave-from {
  opacity: 1;
  transform: scale(1) translateY(0);
}

// Responsive adjustments
@media (max-width: 768px) {
  .notification-dropdown {
    width: calc(100vw - 2rem);
    max-width: 380px;
    right: -1rem;
  }
  
  // Improve touch scrolling
  .dropdown-content {
    scroll-behavior: smooth;
  }
  
  // Larger touch targets for mobile
  .dropdown-header {
    padding: 1.25rem 1rem;
    
    h3 {
      font-size: 1.1rem;
    }
  }
  
  .dropdown-footer {
    padding: 1rem;
  }
}

@media (max-width: 480px) {
  .notification-dropdown {
    border-radius: 16px 16px 0 0; // Rounded top corners only on small screens
    box-shadow: 0 -5px 25px v.$shadow-medium;
  }
}

// Add support for reduced motion
@media (prefers-reduced-motion: reduce) {
  .bell-button,
  .notification-item,
  .mark-all-read-btn,
  .view-more-btn {
    transition: none;
  }
  
  .bell-button.ringing .bell-icon-container {
    animation: none;
  }
  
  .bell-button.ringing .ring-lines {
    animation: none;
  }
  
  .ring-line {
    animation: none !important;
  }
  
  .loading-spinner {
    animation: none;
  }
  
  .connection-status.status-connecting i {
    animation: none;
  }
}

// High contrast mode support
@media (prefers-contrast: high) {
  .bell-button:focus,
  .notification-dropdown:focus,
  .notification-item:focus,
  .mark-all-read-btn:focus,
  .view-more-btn:focus {
    outline: 3px solid;
    outline-offset: 2px;
  }
  
  .unread-badge {
    border: 2px solid v.$white;
  }
  
  .notification-item.unread {
    border-left-width: 4px;
  }
}

// Dark mode styles
[data-theme="dark"] {
  .bell-button {
    &:hover {
      background: #1c2128;
    }
    
    &:active,
    &.touch-active {
      background: #2563eb;
    }
    
    &.active {
      background: #2563eb;
    }
    
    &.has-notifications {
      color: #58a6ff;
      
      .bell-icon {
        color: #58a6ff;
      }
    }
    
    &.ringing .bell-icon {
      color: #58a6ff;
    }
    
    .ring-lines {
      color: #58a6ff;
    }
  }
  
  .notification-dropdown {
    background: #161b22;
    border-color: #30363d;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }
  
  .dropdown-header {
    background: #0d1117;
    border-bottom-color: #30363d;
    
    h3 {
      color: #e6edf3;
    }
    
    .connection-status {
      &.status-connected {
        background: rgba(16, 185, 129, 0.15);
        color: #3fb950;
      }
      
      &.status-connecting {
        background: rgba(59, 130, 246, 0.15);
        color: #58a6ff;
      }
      
      &.status-error,
      &.status-disconnected {
        background: rgba(239, 68, 68, 0.15);
        color: #f85149;
      }
      
      &.status-fallback {
        background: rgba(245, 158, 11, 0.15);
        color: #d29922;
      }
      
      &.status-offline {
        background: rgba(125, 133, 144, 0.15);
        color: #7d8590;
      }
    }
    
    .mark-all-read-btn {
      color: #58a6ff;
      
      &:hover {
        background: rgba(37, 99, 235, 0.15);
      }
      
      &:active {
        background: rgba(37, 99, 235, 0.25);
      }
    }
  }
  
  .connection-warning {
    background: rgba(239, 68, 68, 0.05);
    border-bottom-color: #30363d;
    
    i {
      color: #f85149;
    }
    
    .warning-text p:first-child {
      color: #f85149;
    }
    
    .warning-text p:last-child {
      color: #7d8590;
    }
  }
  
  .fallback-notice {
    background: rgba(245, 158, 11, 0.05);
    border-bottom-color: #30363d;
    
    i {
      color: #d29922;
    }
    
    .notice-text p:first-child {
      color: #d29922;
    }
    
    .notice-text p:last-child {
      color: #7d8590;
    }
  }
  
  .loading-state {
    color: #7d8590;
    
    .loading-spinner {
      border-color: #30363d;
      border-top-color: #58a6ff;
    }
  }
  
  .empty-state {
    color: #7d8590;
  }
  
  .notifications-list {
    .notification-item {
      &:hover {
        background: #0d1117;
      }
      
      &:active,
      &.touch-active {
        background: rgba(37, 99, 235, 0.1);
      }
      
      &.focused {
        background: rgba(37, 99, 235, 0.1);
        border-left-color: #58a6ff;
      }
      
      &.unread {
        background: rgba(37, 99, 235, 0.05);
        border-left-color: #58a6ff;
        
        &:active,
        &.touch-active {
          background: rgba(37, 99, 235, 0.15);
        }
        
        &.focused {
          background: rgba(37, 99, 235, 0.15);
        }
      }
      
      &:not(:last-child) {
        border-bottom-color: #30363d;
      }
    }
  }
  
  .notification-icon {
    &.type-success {
      background: rgba(16, 185, 129, 0.15);
      color: #3fb950;
    }
    
    &.type-warning {
      background: rgba(245, 158, 11, 0.15);
      color: #d29922;
    }
    
    &.type-danger {
      background: rgba(239, 68, 68, 0.15);
      color: #f85149;
    }
    
    &.type-info {
      background: rgba(59, 130, 246, 0.15);
      color: #58a6ff;
    }
  }
  
  .notification-text {
    .notification-title {
      color: #e6edf3;
    }
    
    .notification-message {
      color: #7d8590;
    }
    
    .notification-time {
      color: #6e7681;
    }
  }
  
  .unread-indicator {
    background: #58a6ff;
  }
  
  .dropdown-footer {
    background: #0d1117;
    border-top-color: #30363d;
    
    .view-more-btn {
      border-color: #30363d;
      color: #7d8590;
      
      &:hover {
        background: #1c2128;
        color: #e6edf3;
      }
      
      &:active {
        background: rgba(37, 99, 235, 0.15);
      }
    }
  }
}
</style>