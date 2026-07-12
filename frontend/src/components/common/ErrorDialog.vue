<template>
  <div v-if="show" class="error-dialog-overlay" @click="handleOverlayClick">
    <div class="error-dialog" :class="['severity-' + error.severity, 'type-' + error.error_type]">
      <!-- Header -->
      <div class="error-dialog-header">
        <div class="error-icon">
          <i :class="iconClass"></i>
        </div>
        <div class="error-title">
          <h3>{{ error.title }}</h3>
          <div class="error-code" v-if="error.error_code">
            {{ error.error_code }}
          </div>
        </div>
        <button class="close-button" @click="close" :disabled="!closable">
          <i class="icofont-close"></i>
        </button>
      </div>

      <!-- Humorous Message -->
      <div class="humorous-message" v-if="error.humorous_message">
        <p>{{ error.humorous_message }}</p>
      </div>

      <!-- Main Message -->
      <div class="error-message">
        <p>{{ error.message }}</p>
      </div>

      <!-- Field Errors -->
      <div class="field-errors" v-if="error.field_errors && Object.keys(error.field_errors).length > 0">
        <h4>Field Issues:</h4>
        <ul>
          <li v-for="(fieldError, field) in error.field_errors" :key="field">
            <strong>{{ formatFieldName(field) }}:</strong> {{ fieldError }}
          </li>
        </ul>
      </div>

      <!-- Details (collapsible) -->
      <div class="error-details" v-if="error.details">
        <button 
          class="details-toggle" 
          @click="showDetails = !showDetails"
          type="button"
        >
          <i :class="showDetails ? 'icofont-caret-up' : 'icofont-caret-down'"></i>
          Technical Details
        </button>
        <div class="details-content" v-show="showDetails">
          <pre>{{ error.details }}</pre>
        </div>
      </div>

      <!-- Suggestions -->
      <div class="error-suggestions" v-if="error.suggestions && error.suggestions.length > 0">
        <h4>💡 What you can try:</h4>
        <ul>
          <li v-for="(suggestion, index) in error.suggestions" :key="index">
            {{ suggestion }}
          </li>
        </ul>
      </div>

      <!-- Actions -->
      <div class="error-actions">
        <button 
          class="btn btn-primary" 
          @click="close"
          :disabled="!closable"
        >
          {{ closable ? 'Got it!' : `Please wait... (${countdown}s)` }}
        </button>
        <button 
          class="btn btn-secondary" 
          @click="retry" 
          v-if="retryable"
        >
          Try Again
        </button>
        <button 
          class="btn btn-secondary" 
          @click="reportError" 
          v-if="error.severity === 'critical'"
        >
          Report Issue
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, PropType } from 'vue';

interface ErrorData {
  error_type: string;
  title: string;
  message: string;
  details?: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  humorous_message?: string;
  suggestions?: string[];
  error_code?: string;
  field_errors?: Record<string, string>;
  show_dialog: boolean;
}

const props = defineProps({
  error: {
    type: Object as PropType<ErrorData>,
    required: true
  },
  show: {
    type: Boolean,
    default: false
  },
  retryable: {
    type: Boolean,
    default: false
  },
  autoClose: {
    type: Boolean,
    default: false
  },
  autoCloseDelay: {
    type: Number,
    default: 5000
  }
});

const emit = defineEmits(['close', 'retry', 'report']);

const showDetails = ref(false);
const closable = ref(true);
const countdown = ref(0);
let countdownTimer: any = null;

const iconClass = computed(() => {
  const iconMap = {
    'user_error': 'icofont-warning',
    'validation_error': 'icofont-exclamation-circle',
    'access_error': 'icofont-lock',
    'network_error': 'icofont-wifi-alt',
    'server_error': 'icofont-server',
    'not_found_error': 'icofont-search-document',
    'rate_limit_error': 'icofont-speed-meter',
    'authentication_error': 'icofont-key',
    'permission_error': 'icofont-shield',
    'data_integrity_error': 'icofont-database'
  };
  
  return iconMap[props.error.error_type as keyof typeof iconMap] || 'icofont-warning';
});

const formatFieldName = (field: string): string => {
  // Convert field names like "user_name" or "user -> name" to "User Name"
  return field
    .replace(/[_-]/g, ' ')
    .replace(/ -> /g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
};

const close = () => {
  if (closable.value) {
    emit('close');
  }
};

const retry = () => {
  emit('retry');
};

const reportError = () => {
  emit('report', {
    error: props.error,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href
  });
};

const handleOverlayClick = (event: MouseEvent) => {
  if (event.target === event.currentTarget && closable.value) {
    close();
  }
};

const startCountdown = () => {
  if (!props.autoClose) return;
  
  closable.value = false;
  countdown.value = Math.ceil(props.autoCloseDelay / 1000);
  
  countdownTimer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      closable.value = true;
      clearInterval(countdownTimer);
    }
  }, 1000);
  
  // Auto close after delay
  setTimeout(() => {
    closable.value = true;
    if (props.show) {
      close();
    }
  }, props.autoCloseDelay);
};

onMounted(() => {
  if (props.show && props.autoClose) {
    startCountdown();
  }
});

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }
});

// Handle escape key
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && closable.value) {
    close();
  }
};

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.error-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: v.$shadow-darkest;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(2px);
  animation: fadeIn 0.3s ease-out;
}

.error-dialog {
  background: v.$white;
  border-radius: 12px;
  box-shadow: 0 20px 60px v.$shadow-darker;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  animation: slideIn 0.3s ease-out;
  
  // Severity-based styling
  &.severity-info {
    border-left: 5px solid #17a2b8;
  }
  
  &.severity-warning {
    border-left: 5px solid #ffc107;
  }
  
  &.severity-error {
    border-left: 5px solid #dc3545;
  }
  
  &.severity-critical {
    border-left: 5px solid v.$purple-600;
    box-shadow: 0 20px 60px v.$shadow-purple;
  }
  
  // Type-specific styling
  &.type-user_error {
    .error-dialog-header {
      background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
      border-bottom-color: #ffc107;
    }
    .error-title h3 {
      color: #856404;
    }
  }
  
  &.type-validation_error {
    .error-dialog-header {
      background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
      border-bottom-color: #ffc107;
    }
    .error-title h3 {
      color: #856404;
    }
  }
  
  &.type-access_error {
    .error-dialog-header {
      background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
      border-bottom-color: #dc3545;
    }
    .error-title h3 {
      color: #721c24;
    }
  }
  
  &.type-authentication_error {
    .error-dialog-header {
      background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
      border-bottom-color: #dc3545;
    }
    .error-title h3 {
      color: #721c24;
    }
  }
  
  &.type-server_error {
    .error-dialog-header {
      background: linear-gradient(135deg, #e2d9f3 0%, #d1c4e9 100%);
      border-bottom-color: v.$purple-600;
    }
    .error-title h3 {
      color: #4a148c;
    }
  }
  
  &.type-network_error {
    .error-dialog-header {
      background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
      border-bottom-color: #17a2b8;
    }
    .error-title h3 {
      color: #0c5460;
    }
  }
}

.error-dialog-header {
  display: flex;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e9ecef;
  
  .error-icon {
    font-size: 2.5rem;
    margin-right: 16px;
    
    .severity-info & { color: #17a2b8; }
    .severity-warning & { color: #ffc107; }
    .severity-error & { color: #dc3545; }
    .severity-critical & { color: v.$purple-600; }
  }
  
  .error-title {
    flex: 1;
    
    h3 {
      margin: 0 0 4px 0;
      font-size: 1.25rem;
      font-weight: 600;
      color: #212529;
    }
    
    .error-code {
      font-size: 0.875rem;
      color: #6c757d;
      font-family: 'Courier New', monospace;
    }
  }
  
  .close-button {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: #6c757d;
    cursor: pointer;
    padding: 4px;
    border-radius: v.$radius-btn;
    transition: all 0.2s;
    
    &:hover:not(:disabled) {
      background: #f8f9fa;
      color: #495057;
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.humorous-message {
  padding: 16px 24px;
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  border-left: 4px solid #ffc107;
  margin: 0;
  
  p {
    margin: 0;
    font-style: italic;
    color: #856404;
    font-size: 1rem;
    line-height: 1.4;
  }
}

.error-message {
  padding: 20px 24px;
  
  p {
    margin: 0;
    font-size: 1rem;
    line-height: 1.5;
    color: #495057;
  }
}

.field-errors {
  padding: 0 24px 20px;
  
  h4 {
    margin: 0 0 12px 0;
    font-size: 1rem;
    color: #dc3545;
    font-weight: 600;
  }
  
  ul {
    margin: 0;
    padding-left: 20px;
    
    li {
      margin-bottom: 8px;
      color: #495057;
      
      strong {
        color: #dc3545;
      }
    }
  }
}

.error-details {
  padding: 0 24px 20px;
  
  .details-toggle {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: v.$radius-btn;
    padding: 8px 12px;
    font-size: 0.875rem;
    color: #495057;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.2s;
    
    &:hover {
      background: #e9ecef;
    }
    
    i {
      font-size: 0.75rem;
    }
  }
  
  .details-content {
    margin-top: 12px;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 12px;
    
    pre {
      margin: 0;
      font-size: 0.75rem;
      color: #495057;
      white-space: pre-wrap;
      word-break: break-word;
    }
  }
}

.error-suggestions {
  padding: 0 24px 20px;
  
  h4 {
    margin: 0 0 12px 0;
    font-size: 1rem;
    color: #28a745;
    font-weight: 600;
  }
  
  ul {
    margin: 0;
    padding-left: 20px;
    
    li {
      margin-bottom: 8px;
      color: #495057;
      line-height: 1.4;
    }
  }
}

.error-actions {
  padding: 20px 24px;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  
  .btn {
    padding: 10px 20px;
    border-radius: v.$radius-btn;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.875rem;
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    &.btn-primary {
      background: #007bff;
      color: v.$white;
      
      &:hover:not(:disabled) {
        background: #0056b3;
      }
    }
    
    &.btn-secondary {
      background: #6c757d;
      color: v.$white;
      
      &:hover:not(:disabled) {
        background: #545b62;
      }
    }
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

// Dark mode styles
[data-theme="dark"] {
  .error-dialog-overlay {
    background: rgba(0, 0, 0, 0.7);
  }

  .error-dialog {
    background: #161b22;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
    
    &.severity-info {
      border-left-color: #58a6ff;
      
      .error-dialog-header {
        background: linear-gradient(135deg, rgba(88, 166, 255, 0.15) 0%, rgba(88, 166, 255, 0.05) 100%);
      }
    }
    
    &.severity-warning {
      border-left-color: #d29922;
      
      .error-dialog-header {
        background: linear-gradient(135deg, rgba(210, 153, 34, 0.15) 0%, rgba(210, 153, 34, 0.05) 100%);
      }
    }
    
    &.severity-error {
      border-left-color: #f85149;
      
      .error-dialog-header {
        background: linear-gradient(135deg, rgba(248, 81, 73, 0.15) 0%, rgba(248, 81, 73, 0.05) 100%);
      }
    }
    
    &.severity-critical {
      border-left-color: #bc8cff;
      box-shadow: 0 20px 60px rgba(188, 140, 255, 0.3);
      
      .error-dialog-header {
        background: linear-gradient(135deg, rgba(188, 140, 255, 0.15) 0%, rgba(188, 140, 255, 0.05) 100%);
      }
    }
    
    &.type-user_error,
    &.type-validation_error,
    &.type-access_error,
    &.type-authentication_error,
    &.type-server_error,
    &.type-network_error {
      .error-title h3 {
        color: #e6edf3;
      }
    }
  }

  .error-dialog-header {
    border-bottom-color: #30363d;
    
    .error-icon {
      .severity-info & { color: #58a6ff; }
      .severity-warning & { color: #d29922; }
      .severity-error & { color: #f85149; }
      .severity-critical & { color: #bc8cff; }
    }
    
    .error-title {
      h3 {
        color: #e6edf3;
      }
      
      .error-code {
        color: #7d8590;
      }
    }
    
    .close-button {
      color: #7d8590;
      
      &:hover:not(:disabled) {
        background: #0d1117;
        color: #e6edf3;
      }
    }
  }

  .humorous-message {
    background: linear-gradient(135deg, rgba(88, 166, 255, 0.1) 0%, rgba(88, 166, 255, 0.05) 100%);
    border-left-color: #58a6ff;
    
    p {
      color: #7d8590;
      font-style: italic;
    }
  }

  .error-message {
    p {
      color: #7d8590;
    }
  }

  .field-errors {
    h4 {
      color: #f85149;
    }
    
    ul li {
      color: #7d8590;
      
      strong {
        color: #f85149;
      }
    }
  }

  .error-details {
    .details-toggle {
      background: #0d1117;
      border-color: #30363d;
      color: #e6edf3;
      
      &:hover {
        background: #21262d;
      }
    }
    
    .details-content {
      background: #0d1117;
      border-color: #30363d;
      
      pre {
        color: #7d8590;
      }
    }
  }

  .error-suggestions {
    h4 {
      color: #58a6ff;
    }
    
    ul li {
      color: #7d8590;
    }
  }

  .error-actions {
    border-top-color: #30363d;
    
    .btn {
      &.btn-primary {
        background: #2563eb;
        
        &:hover:not(:disabled) {
          background: #1d4ed8;
        }
      }
      
      &.btn-secondary {
        background: #21262d;
        color: #e6edf3;
        
        &:hover:not(:disabled) {
          background: #30363d;
        }
      }
    }
  }
}

// Mobile responsiveness
@media (max-width: 768px) {
  .error-dialog {
    width: 95%;
    margin: 20px;
    max-height: 90vh;
  }
  
  .error-dialog-header {
    padding: 16px 20px 12px;
    
    .error-icon {
      font-size: 2rem;
      margin-right: 12px;
    }
    
    .error-title h3 {
      font-size: 1.125rem;
    }
  }
  
  .humorous-message,
  .error-message,
  .field-errors,
  .error-details,
  .error-suggestions {
    padding-left: 20px;
    padding-right: 20px;
  }
  
  .error-actions {
    padding: 16px 20px;
    flex-direction: column;
    
    .btn {
      width: 100%;
    }
  }
}
</style>