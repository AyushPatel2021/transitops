<template>
  <transition name="dialog-fade">
    <div v-if="show" class="dialog-overlay" @mousedown.self="handleOverlayClick">
      <div class="dialog-container" :class="`dialog-${type}`">
        <!-- Header with Icon and Title -->
        <div class="dialog-header">
          <div class="icon-wrapper">
            <AlertCircle v-if="type === 'warning'" class="dialog-icon icon-warning" />
            <AlertTriangle v-else-if="type === 'error'" class="dialog-icon icon-error" />
            <CheckCircle v-else-if="type === 'success'" class="dialog-icon icon-success" />
            <Info v-else class="dialog-icon icon-info" />
          </div>
          <h3 class="dialog-title">{{ title }}</h3>
        </div>
        
        <!-- Content -->
        <div class="dialog-content">
          <p class="dialog-message">{{ message }}</p>
        </div>
        
        <!-- Actions -->
        <div class="dialog-actions">
          <button 
            class="btn btn-primary" 
            @click="handleConfirm"
            :disabled="loading"
          >
            <span v-if="loading" class="mini-spinner"></span>
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { AlertCircle, AlertTriangle, CheckCircle, Info } from 'lucide-vue-next';
import { onMounted, onUnmounted } from 'vue';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Alert'
  },
  message: {
    type: String,
    required: true
  },
  type: {
    type: String as () => 'info' | 'success' | 'warning' | 'error',
    default: 'info'
  },
  confirmText: {
    type: String,
    default: 'OK'
  },
  loading: {
    type: Boolean,
    default: false
  },
  closeOnOverlay: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['confirm', 'close']);

const handleConfirm = () => {
  emit('confirm');
  emit('close');
};

const handleOverlayClick = () => {
  if (props.closeOnOverlay) {
    emit('close');
  }
};

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.show) {
    handleConfirm();
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleEscape);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleEscape);
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.dialog-container {
  background: v.$white;
  border-radius: 16px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.2);
  width: 420px;
  max-width: 90vw;
  overflow: hidden;
  animation: slideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.dialog-header {
  padding: 2rem 2rem 1rem;
  text-align: center;
  
  .icon-wrapper {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin-bottom: 1.25rem;
    position: relative;
    
    &::before {
      content: '';
      position: absolute;
      inset: -8px;
      border-radius: 50%;
      opacity: 0.1;
    }
  }
  
  .dialog-icon {
    width: 48px;
    height: 48px;
    position: relative;
    z-index: 1;
  }
}

.dialog-info {
  .icon-wrapper {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    
    &::before {
      background: #2196f3;
    }
    
    .icon-info {
      color: #1976d2;
    }
  }
}

.dialog-success {
  .icon-wrapper {
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    
    &::before {
      background: #4caf50;
    }
    
    .icon-success {
      color: #2e7d32;
    }
  }
}

.dialog-warning {
  .icon-wrapper {
    background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
    
    &::before {
      background: #ffc107;
    }
    
    .icon-warning {
      color: #f57c00;
    }
  }
}

.dialog-error {
  .icon-wrapper {
    background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
    
    &::before {
      background: #f44336;
    }
    
    .icon-error {
      color: #c62828;
    }
  }
}

.dialog-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: -0.02em;
}

.dialog-content {
  padding: 0 2rem 2rem;
  text-align: center;
}

.dialog-message {
  margin: 0;
  font-size: 1rem;
  color: #666;
  line-height: 1.6;
}

.dialog-actions {
  display: flex;
  gap: 0.75rem;
  padding: 1.5rem 2rem;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.btn {
  flex: 1;
  padding: 0.875rem 1.5rem;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9375rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease;
  border: none;
  letter-spacing: 0.01em;
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &:active:not(:disabled) {
    transform: scale(0.98);
  }
  
  &.btn-primary {
    background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
    color: v.$white;
    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
    
    &:hover:not(:disabled) { 
      box-shadow: 0 6px 16px rgba(33, 150, 243, 0.4);
      transform: translateY(-2px);
    }
  }
}

.mini-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid v.$white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
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

.dialog-fade-enter-active, .dialog-fade-leave-active {
  transition: opacity 0.25s ease;
  
  .dialog-container {
    transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.25s ease;
  }
}

.dialog-fade-enter-from, .dialog-fade-leave-to {
  opacity: 0;
  
  .dialog-container {
    transform: scale(0.9) translateY(-20px);
    opacity: 0;
  }
}

// Dark Mode Styles
[data-theme="dark"] {
  .dialog-overlay {
    background: rgba(0, 0, 0, 0.7);
  }

  .dialog-container {
    background: #161b22;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4);
  }

  .dialog-title {
    color: #e6edf3;
  }

  .dialog-message {
    color: #7d8590;
  }

  .dialog-info {
    .icon-wrapper {
      background: linear-gradient(135deg, rgba(88, 166, 255, 0.15) 0%, rgba(88, 166, 255, 0.25) 100%);
    }
    .icon-info {
      color: #58a6ff;
    }
  }

  .dialog-success {
    .icon-wrapper {
      background: linear-gradient(135deg, rgba(63, 185, 80, 0.15) 0%, rgba(63, 185, 80, 0.25) 100%);
    }
    .icon-success {
      color: #3fb950;
    }
  }

  .dialog-warning {
    .icon-wrapper {
      background: linear-gradient(135deg, rgba(210, 153, 34, 0.15) 0%, rgba(210, 153, 34, 0.25) 100%);
    }
    .icon-warning {
      color: #d29922;
    }
  }

  .dialog-error {
    .icon-wrapper {
      background: linear-gradient(135deg, rgba(248, 81, 73, 0.15) 0%, rgba(248, 81, 73, 0.25) 100%);
    }
    .icon-error {
      color: #f85149;
    }
  }

  .dialog-actions {
    background: #0d1117;
    border-top: 1px solid #30363d;
    
    .btn-primary {
      background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
      
      &:hover:not(:disabled) {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
      }
    }
    
    .btn-secondary {
      background: #21262d;
      color: #e6edf3;
      border: 1px solid #30363d;
      
      &:hover:not(:disabled) {
        background: #30363d;
        border-color: #484f58;
      }
    }
  }

  .mini-spinner {
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid #e6edf3;
  }
}

// Mobile responsiveness
@media (max-width: 768px) {
  .dialog-container {
    width: 95vw;
    margin: 1rem;
  }
  
  .dialog-header {
    padding: 1.5rem 1.5rem 0.75rem;
    
    .icon-wrapper {
      width: 64px;
      height: 64px;
      margin-bottom: 1rem;
    }
    
    .dialog-icon {
      width: 40px;
      height: 40px;
    }
  }
  
  .dialog-title {
    font-size: 1.25rem;
  }
  
  .dialog-content {
    padding: 0 1.5rem 1.5rem;
  }
  
  .dialog-message {
    font-size: 0.9375rem;
  }
  
  .dialog-actions {
    padding: 1.25rem 1.5rem;
  }
}
</style>
