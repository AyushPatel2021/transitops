<template>
  <transition name="dialog-fade">
    <div v-if="show" class="dialog-overlay" @mousedown.self="handleOverlayClick">
      <div class="dialog-container">
        <!-- Header -->
        <div class="dialog-header">
          <h3 class="dialog-title">{{ title }}</h3>
          <p v-if="message" class="dialog-subtitle">{{ message }}</p>
        </div>
        
        <!-- Content -->
        <div class="dialog-content">
          <div class="input-wrapper">
            <input
              ref="inputRef"
              v-model="inputValue"
              :type="inputType"
              :placeholder="placeholder"
              class="form-input"
              :class="{ 'input-invalid': showError && !inputValue }"
              @keyup.enter="handleConfirm"
              @keyup.esc="handleCancel"
            />
            <span v-if="showError && !inputValue" class="error-text">This field is required</span>
          </div>
        </div>
        
        <!-- Actions -->
        <div class="dialog-actions">
          <button 
            class="btn btn-secondary" 
            @click="handleCancel"
            :disabled="loading"
          >
            {{ cancelText }}
          </button>
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
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Input'
  },
  message: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Enter value...'
  },
  defaultValue: {
    type: String,
    default: ''
  },
  inputType: {
    type: String as () => 'text' | 'number' | 'email' | 'password',
    default: 'text'
  },
  required: {
    type: Boolean,
    default: true
  },
  confirmText: {
    type: String,
    default: 'OK'
  },
  cancelText: {
    type: String,
    default: 'Cancel'
  },
  loading: {
    type: Boolean,
    default: false
  },
  closeOnOverlay: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['confirm', 'cancel', 'close']);

const inputRef = ref<HTMLInputElement | null>(null);
const inputValue = ref('');
const showError = ref(false);

// Watch for show prop to reset and focus input
watch(() => props.show, (newVal) => {
  if (newVal) {
    inputValue.value = props.defaultValue;
    showError.value = false;
    nextTick(() => {
      inputRef.value?.focus();
    });
  }
});

const handleConfirm = () => {
  if (props.required && !inputValue.value) {
    showError.value = true;
    return;
  }
  
  emit('confirm', inputValue.value);
};

const handleCancel = () => {
  emit('cancel');
  emit('close');
};

const handleOverlayClick = () => {
  if (props.closeOnOverlay) {
    handleCancel();
  }
};

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.show) {
    handleCancel();
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
  width: 480px;
  max-width: 90vw;
  overflow: hidden;
  animation: slideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.dialog-header {
  padding: 2rem 2rem 1rem;
  text-align: center;
}

.dialog-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: -0.02em;
}

.dialog-subtitle {
  margin: 0.5rem 0 0;
  font-size: 0.9375rem;
  color: #666;
  line-height: 1.5;
}

.dialog-content {
  padding: 0 2rem 2rem;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 1rem;
  color: #1a1a1a;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  background: #fafafa;
  
  &:hover {
    border-color: #bdbdbd;
    background: v.$white;
  }
  
  &:focus {
    outline: none;
    border-color: #2196f3;
    background: v.$white;
    box-shadow: 0 0 0 4px rgba(33, 150, 243, 0.1);
  }
  
  &.input-invalid {
    border-color: #f44336;
    background: #fff5f5;
    
    &:focus {
      box-shadow: 0 0 0 4px rgba(244, 67, 54, 0.1);
    }
  }
  
  &::placeholder {
    color: #999;
  }
}

.error-text {
  font-size: 0.8125rem;
  color: #f44336;
  font-weight: 500;
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
  
  &.btn-secondary {
    background: v.$white;
    color: #666;
    border: 2px solid #e0e0e0;
    box-shadow: none;
    
    &:hover:not(:disabled) { 
      background: #f5f5f5;
      border-color: #bdbdbd;
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

// Dark mode styles
[data-theme="dark"] {
  .dialog-overlay {
    background: rgba(0, 0, 0, 0.7);
  }

  .dialog-container {
    background: #161b22;
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.6);
  }

  .dialog-title {
    color: #e6edf3;
  }

  .dialog-subtitle {
    color: #7d8590;
  }

  .form-input {
    background: #0d1117;
    border-color: #30363d;
    color: #e6edf3;
    
    &:hover {
      border-color: #484f58;
      background: #0d1117;
    }
    
    &:focus {
      border-color: #58a6ff;
      background: #0d1117;
      box-shadow: 0 0 0 4px rgba(88, 166, 255, 0.1);
    }
    
    &.input-invalid {
      border-color: #f85149;
      background: rgba(248, 81, 73, 0.1);
      
      &:focus {
        box-shadow: 0 0 0 4px rgba(248, 81, 73, 0.1);
      }
    }
    
    &::placeholder {
      color: #7d8590;
    }
  }

  .error-text {
    color: #f85149;
  }

  .dialog-actions {
    background: #0d1117;
    border-top-color: #30363d;
  }

  .btn {
    &.btn-primary {
      background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
      
      &:hover:not(:disabled) { 
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
      }
    }
    
    &.btn-secondary {
      background: #21262d;
      color: #e6edf3;
      border-color: #30363d;
      
      &:hover:not(:disabled) { 
        background: #30363d;
        border-color: #484f58;
      }
    }
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
  }
  
  .dialog-title {
    font-size: 1.25rem;
  }
  
  .dialog-subtitle {
    font-size: 0.875rem;
  }
  
  .dialog-content {
    padding: 0 1.5rem 1.5rem;
  }
  
  .dialog-actions {
    padding: 1.25rem 1.5rem;
    flex-direction: column;
    
    .btn {
      width: 100%;
    }
  }
}
</style>
