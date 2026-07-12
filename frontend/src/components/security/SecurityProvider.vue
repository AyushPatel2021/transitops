<!--
  Security Provider Component
  
  Provides application-wide security monitoring and validation.
  Automatically initializes security service and handles security events.
  
  Requirements: 6.2, 6.5, 8.1, 8.4, 8.5
-->

<template>
  <div class="security-provider">
    <!-- Security Status Indicator (Development Mode) -->
    <div 
      v-if="showSecurityIndicator && !securityStatus.isSecure" 
      class="security-alert"
      @click="showSecurityDetails = !showSecurityDetails"
    >
      <div class="security-alert-icon">🔒</div>
      <div class="security-alert-text">
        Security Issues Detected ({{ securityStatus.issues.length }})
      </div>
    </div>

    <!-- Security Details Modal (Development Mode) -->
    <div v-if="showSecurityDetails" class="security-modal" @click="showSecurityDetails = false">
      <div class="security-modal-content" @click.stop>
        <div class="security-modal-header">
          <h3>Security Status</h3>
          <button @click="showSecurityDetails = false" class="close-btn">×</button>
        </div>
        
        <div class="security-modal-body">
          <div class="security-status">
            <div class="status-item">
              <strong>Overall Status:</strong>
              <span :class="{ 'secure': securityStatus.isSecure, 'insecure': !securityStatus.isSecure }">
                {{ securityStatus.isSecure ? 'Secure' : 'Issues Detected' }}
              </span>
            </div>
            
            <div class="status-item">
              <strong>Last Audit:</strong>
              {{ securityStatus.lastAudit ? formatDate(securityStatus.lastAudit) : 'Never' }}
            </div>
            
            <div class="status-item">
              <strong>Migration Status:</strong>
              {{ securityStatus.migratedData ? 'Completed' : 'Not Required' }}
            </div>
          </div>

          <div v-if="securityStatus.issues.length > 0" class="security-issues">
            <h4>Security Issues:</h4>
            <ul>
              <li v-for="issue in securityStatus.issues" :key="issue" class="issue-item">
                {{ issue }}
              </li>
            </ul>
          </div>

          <div v-if="recommendations.length > 0" class="security-recommendations">
            <h4>Recommendations:</h4>
            <ul>
              <li v-for="rec in recommendations" :key="rec" class="recommendation-item">
                {{ rec }}
              </li>
            </ul>
          </div>

          <div class="security-actions">
            <button @click="performAudit" :disabled="isPerformingAudit" class="audit-btn">
              {{ isPerformingAudit ? 'Auditing...' : 'Force Audit' }}
            </button>
            <button @click="performCleanup" :disabled="isPerformingCleanup" class="cleanup-btn">
              {{ isPerformingCleanup ? 'Cleaning...' : 'Cleanup localStorage' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Session Warning Modal -->
    <div v-if="showSessionWarning" class="session-warning-modal">
      <div class="session-warning-content">
        <div class="session-warning-header">
          <h3>⚠️ Session Expiring Soon</h3>
        </div>
        
        <div class="session-warning-body">
          <p>Your session will expire in {{ sessionTimeRemaining }} seconds.</p>
          <p>Would you like to extend your session?</p>
          
          <div class="session-warning-actions">
            <button @click="extendSession" class="extend-btn">Extend Session</button>
            <button @click="dismissSessionWarning" class="dismiss-btn">Dismiss</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Application Content -->
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { securityService, useSecurity } from '../../services/securityService';
import { useUserStore } from '../../stores/userStore';
import { formatDateTime } from '../../utils/dateUtils';

// Props
interface Props {
  enableSecurityIndicator?: boolean;
  enableSessionWarnings?: boolean;
  autoInitialize?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  enableSecurityIndicator: true,
  enableSessionWarnings: true,
  autoInitialize: true
});

// Composables
const security = useSecurity();
const userStore = useUserStore();

// State
const securityStatus = ref(security.getStatus());
const recommendations = ref<string[]>([]);
const showSecurityIndicator = ref(props.enableSecurityIndicator && import.meta.env.DEV);
const showSecurityDetails = ref(false);
const isPerformingAudit = ref(false);
const isPerformingCleanup = ref(false);

// Session warning state
const showSessionWarning = ref(false);
const sessionTimeRemaining = ref(0);
const sessionWarningTimer = ref<number | null>(null);

// Computed
const isDevelopment = computed(() => import.meta.env.DEV);

// Methods
const formatDate = (date: Date): string => {
  return formatDateTime(date);
};

const updateSecurityStatus = async (): Promise<void> => {
  securityStatus.value = security.getStatus();
  recommendations.value = security.getRecommendations();
};

const performAudit = async (): Promise<void> => {
  isPerformingAudit.value = true;
  try {
    await security.forceAudit();
    await updateSecurityStatus();
  } catch (error) {
    // Silent error handling
  } finally {
    isPerformingAudit.value = false;
  }
};

const performCleanup = async (): Promise<void> => {
  isPerformingCleanup.value = true;
  try {
    // Import cleanup function dynamically
    const { cleanupLocalStorage } = await import('../../utils/securityValidation');
    const result = cleanupLocalStorage();
    
    // Refresh security status
    await performAudit();
  } catch (error) {
    // Silent error handling
  } finally {
    isPerformingCleanup.value = false;
  }
};

// Session warning handlers
const handleSessionWarning = (timeRemaining: number): void => {
  if (!props.enableSessionWarnings) return;
  
  sessionTimeRemaining.value = timeRemaining;
  showSessionWarning.value = true;
  
  // Update countdown
  if (sessionWarningTimer.value) {
    clearInterval(sessionWarningTimer.value);
  }
  
  sessionWarningTimer.value = setInterval(() => {
    sessionTimeRemaining.value--;
    if (sessionTimeRemaining.value <= 0) {
      showSessionWarning.value = false;
      if (sessionWarningTimer.value) {
        clearInterval(sessionWarningTimer.value);
        sessionWarningTimer.value = null;
      }
    }
  }, 1000);
};

const handleSessionExpired = (): void => {
  showSessionWarning.value = false;
  if (sessionWarningTimer.value) {
    clearInterval(sessionWarningTimer.value);
    sessionWarningTimer.value = null;
  }
  
  // Session expired - user will be logged out automatically by UserStore
};

const extendSession = async (): Promise<void> => {
  try {
    await userStore.refreshToken();
    showSessionWarning.value = false;
    
    if (sessionWarningTimer.value) {
      clearInterval(sessionWarningTimer.value);
      sessionWarningTimer.value = null;
    }
    
  } catch (error) {
    // Let the session expire naturally
  }
};

const dismissSessionWarning = (): void => {
  showSessionWarning.value = false;
  
  if (sessionWarningTimer.value) {
    clearInterval(sessionWarningTimer.value);
    sessionWarningTimer.value = null;
  }
};

// Lifecycle
onMounted(async () => {
  if (props.autoInitialize) {
    try {
      // Initialize security service
      await securityService.initialize();
      
      // Setup session warning listeners
      if (props.enableSessionWarnings) {
        userStore.onSessionWarning(handleSessionWarning);
        userStore.onSessionExpired(handleSessionExpired);
      }
      
      // Initial security status update
      await updateSecurityStatus();
      
      // Setup periodic status updates
      const statusUpdateInterval = setInterval(updateSecurityStatus, 30000); // 30 seconds
      
      // Cleanup on unmount
      onUnmounted(() => {
        clearInterval(statusUpdateInterval);
        if (sessionWarningTimer.value) {
          clearInterval(sessionWarningTimer.value);
        }
      });
      
    } catch (error) {
      // Silent error handling
    }
  }
});

onUnmounted(() => {
  if (sessionWarningTimer.value) {
    clearInterval(sessionWarningTimer.value);
  }
});

// Expose methods for parent components
defineExpose({
  performAudit,
  performCleanup,
  getSecurityStatus: () => securityStatus.value,
  getRecommendations: () => recommendations.value
});
</script>

<style scoped>
.security-provider {
  position: relative;
  width: 100%;
  height: 100%;
}

/* Security Alert Indicator */
.security-alert {
  position: fixed;
  top: 20px;
  right: 20px;
  background: v.$danger-color;
  color: v.$white;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  z-index: 9999;
  box-shadow: 0 4px 12px v.$shadow-red-button;
  animation: pulse 2s infinite;
}

.security-alert:hover {
  filter: brightness(0.9);
}

.security-alert-icon {
  font-size: 18px;
}

.security-alert-text {
  font-size: 14px;
  font-weight: 500;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* Security Modal */
.security-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: v.$overlay-modal;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.security-modal-content {
  background: v.$white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px v.$shadow-darker;
}

.security-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid v.$border-color;
}

.security-modal-header h3 {
  margin: 0;
  color: v.$text-primary;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: v.$text-secondary;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: v.$text-primary;
}

.security-modal-body {
  padding: 20px;
}

.security-status {
  margin-bottom: 20px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid v.$skeleton-light;
}

.status-item:last-child {
  border-bottom: none;
}

.secure {
  color: v.$success-color;
  font-weight: 500;
}

.insecure {
  color: v.$danger-color;
  font-weight: 500;
}

.security-issues,
.security-recommendations {
  margin-bottom: 20px;
}

.security-issues h4,
.security-recommendations h4 {
  margin: 0 0 10px 0;
  color: v.$text-primary;
}

.issue-item {
  color: v.$danger-color;
  margin-bottom: 5px;
}

.recommendation-item {
  color: v.$warning-color;
  margin-bottom: 5px;
}

.security-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.audit-btn,
.cleanup-btn {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.audit-btn {
  background: v.$primary-color;
  color: v.$white;
}

.audit-btn:hover:not(:disabled) {
  background: v.$primary-hover;
}

.cleanup-btn {
  background: v.$warning-color;
  color: v.$white;
}

.cleanup-btn:hover:not(:disabled) {
  filter: brightness(0.9);
}

.audit-btn:disabled,
.cleanup-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Session Warning Modal */
.session-warning-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: v.$black-transparent-70;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
}

.session-warning-content {
  background: v.$white;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 20px 40px v.$shadow-darker;
}

.session-warning-header {
  padding: 20px;
  border-bottom: 1px solid v.$border-color;
  text-align: center;
}

.session-warning-header h3 {
  margin: 0;
  color: v.$warning-color;
}

.session-warning-body {
  padding: 20px;
  text-align: center;
}

.session-warning-body p {
  margin: 0 0 15px 0;
  color: v.$text-primary;
}

.session-warning-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}

.extend-btn,
.dismiss-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.extend-btn {
  background: v.$success-color;
  color: v.$white;
}

.extend-btn:hover {
  filter: brightness(0.9);
}

.dismiss-btn {
  background: v.$danger-color;
  color: v.$white;
}

.dismiss-btn:hover {
  filter: brightness(0.9);
}

/* Responsive Design */
@media (max-width: 768px) {
  .security-alert {
    top: 10px;
    right: 10px;
    padding: 10px 12px;
  }

  .security-modal-content {
    width: 95%;
    margin: 20px;
  }

  .security-actions {
    flex-direction: column;
  }

  .session-warning-actions {
    flex-direction: column;
  }
}
</style>