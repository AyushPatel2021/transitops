<template>
  <div v-if="show" class="confirm-dialog-overlay" @click="handleOverlayClick">
    <div class="confirm-dialog" :class="['severity-' + severity]">
      <!-- Header -->
      <div class="confirm-dialog-header">
        <div class="confirm-icon">
          <AlertTriangle v-if="severity === 'warning' || severity === 'danger'" class="icon-lg" />
          <Info v-else class="icon-lg" />
        </div>
        <div class="confirm-title">
          <h3>{{ title }}</h3>
        </div>
        <button class="close-button" @click="$emit('cancel')">
          <X class="icon-sm" />
        </button>
      </div>

      <!-- Message -->
      <div class="confirm-message">
        <p>{{ message }}</p>
      </div>

      <!-- Actions -->
      <div class="confirm-actions">
        <button 
          class="btn btn-secondary" 
          @click="$emit('cancel')"
        >
          {{ cancelLabel }}
        </button>
        <button 
          class="btn" 
          :class="severity === 'danger' ? 'btn-danger' : 'btn-primary'"
          @click="$emit('confirm')"
          :disabled="loading"
        >
          <span v-if="loading" class="mini-spinner"></span>
          {{ confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { AlertTriangle, Info, X } from 'lucide-vue-next';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Confirm Action'
  },
  message: {
    type: String,
    required: true
  },
  confirmLabel: {
    type: String,
    default: 'Confirm'
  },
  cancelLabel: {
    type: String,
    default: 'Cancel'
  },
  severity: {
    type: String,
    default: 'warning', // 'info', 'warning', 'danger'
    validator: (value: string) => ['info', 'warning', 'danger'].includes(value)
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['confirm', 'cancel']);

const handleOverlayClick = (event: MouseEvent) => {
  if (event.target === event.currentTarget) {
    emit('cancel');
  }
};

// Handle escape key
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.show) {
    emit('cancel');
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
@use "sass:color";
@use "../../styles/variables" as v;

.confirm-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: v.$black-transparent-40;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(2px);
  animation: fadeIn 0.15s ease-out;
}

.confirm-dialog {
  background: v.$white;
  border-radius: 8px;
  box-shadow: 0 10px 25px -5px v.$shadow-light, 0 8px 10px -6px v.$shadow-light;
  max-width: 450px;
  width: 90%;
  animation: scaleIn 0.15s ease-out;
  overflow: hidden;
  
  &.severity-danger {
    border-top: 4px solid v.$danger-color;
  }
  &.severity-warning {
    border-top: 4px solid v.$warning-color;
  }
  &.severity-info {
    border-top: 4px solid v.$info-color;
  }
}

.confirm-dialog-header {
  display: flex;
  align-items: center;
  padding: 1.25rem 1.5rem 0.75rem;
  
  .confirm-icon {
    margin-right: 12px;
    display: flex;
    align-items: center;
    
    .severity-danger & { color: v.$danger-color; }
    .severity-warning & { color: v.$warning-color; }
    .severity-info & { color: v.$info-color; }
  }
  
  .confirm-title {
    flex: 1;
    h3 {
      margin: 0;
      font-size: 1.125rem;
      font-weight: 600;
      color: v.$text-primary;
    }
  }
  
  .close-button {
    background: none;
    border: none;
    color: v.$text-secondary;
    cursor: pointer;
    padding: 4px;
    border-radius: v.$radius-btn;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:hover {
      background: v.$bg-main;
      color: v.$text-primary;
    }
  }
}

.confirm-message {
  padding: 0.5rem 1.5rem 1.25rem;
  
  p {
    margin: 0;
    font-size: 0.9375rem;
    line-height: 1.5;
    color: v.$text-secondary;
  }
}

.confirm-actions {
  padding: 1rem 1.5rem 1.25rem;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  
  .btn {
    padding: 0.5rem 1rem;
    border-radius: v.$radius-btn;
    font-weight: 500;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid transparent;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    &.btn-primary {
      background: v.$primary-color;
      color: v.$white;
      &:hover:not(:disabled) {
        background: v.$primary-hover;
      }
    }
    
    &.btn-danger {
      background: v.$danger-color;
      color: v.$white;
      &:hover:not(:disabled) {
        filter: brightness(0.9);
      }
    }
    
    &.btn-secondary {
      background: v.$white;
      border-color: v.$border-color;
      color: v.$text-primary;
      &:hover:not(:disabled) {
        background: v.$bg-main;
      }
    }
  }
}

.mini-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid v.$white-transparent-30;
  border-top: 2px solid v.$white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.icon-lg {
  width: 24px;
  height: 24px;
}
.icon-sm {
  width: 18px;
  height: 18px;
}

// Dark Mode Styles
[data-theme="dark"] {
  .confirm-dialog-overlay {
    background: rgba(0, 0, 0, 0.7);
  }

  .confirm-dialog {
    background: #161b22;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4);
    
    &.severity-danger {
      border-top: 4px solid #f85149;
    }
    &.severity-warning {
      border-top: 4px solid #d29922;
    }
    &.severity-info {
      border-top: 4px solid #58a6ff;
    }
  }

  .confirm-dialog-header {
    .confirm-icon {
      .severity-danger & { color: #f85149; }
      .severity-warning & { color: #d29922; }
      .severity-info & { color: #58a6ff; }
    }
    
    .confirm-title h3 {
      color: #e6edf3;
    }
    
    .close-button {
      color: #7d8590;
      
      &:hover {
        background: #0d1117;
        color: #e6edf3;
      }
    }
  }

  .confirm-message p {
    color: #7d8590;
  }

  .confirm-actions {
    .btn-primary {
      background: #2563eb;
      
      &:hover:not(:disabled) {
        background: #1d4ed8;
      }
    }
    
    .btn-danger {
      background: #f85149;
      
      &:hover:not(:disabled) {
        background: #da3633;
      }
    }
    
    .btn-secondary {
      background: #161b22;
      border-color: #30363d;
      color: #e6edf3;
      
      &:hover:not(:disabled) {
        background: #0d1117;
        border-color: #7d8590;
      }
    }
  }

  .mini-spinner {
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid #e6edf3;
  }
}
</style>
