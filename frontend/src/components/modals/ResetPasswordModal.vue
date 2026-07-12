<template>
  <div v-if="isVisible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <div class="modal-header">
        <h3 class="modal-title">Reset Password</h3>
        <button class="modal-close" @click="closeModal">
          <X :size="20" />
        </button>
      </div>
      
      <div class="modal-body">
        <div class="user-info">
          <p><strong>User:</strong> {{ userName }}</p>
          <p><strong>Email:</strong> {{ userEmail }}</p>
        </div>
        
        <form @submit.prevent="handleSubmit" class="reset-form">
          <div class="form-group">
            <label for="newPassword" class="form-label">New Password</label>
            <input
              id="newPassword"
              v-model="formData.newPassword"
              type="password"
              class="form-input"
              :class="{ 'error': errors.newPassword }"
              placeholder="Enter new password"
              required
            />
            <div v-if="errors.newPassword" class="error-message">
              {{ errors.newPassword }}
            </div>
          </div>
          
          <div class="form-group">
            <label for="confirmPassword" class="form-label">Confirm Password</label>
            <input
              id="confirmPassword"
              v-model="formData.confirmPassword"
              type="password"
              class="form-input"
              :class="{ 'error': errors.confirmPassword }"
              placeholder="Confirm new password"
              required
            />
            <div v-if="errors.confirmPassword" class="error-message">
              {{ errors.confirmPassword }}
            </div>
          </div>
          
          <div class="password-requirements">
            <p class="requirements-title">Password Requirements:</p>
            <ul class="requirements-list">
              <li :class="{ 'valid': hasMinLength }">At least 8 characters</li>
              <li :class="{ 'valid': hasLetter }">At least one letter</li>
              <li :class="{ 'valid': hasNumber }">At least one number</li>
            </ul>
          </div>
        </form>
      </div>
      
      <div class="modal-footer">
        <button 
          type="button" 
          class="btn btn-secondary" 
          @click="closeModal"
          :disabled="isLoading"
        >
          Cancel
        </button>
        <button 
          type="button" 
          class="btn btn-primary" 
          @click="handleSubmit"
          :disabled="!isFormValid || isLoading"
        >
          <span v-if="isLoading">Resetting...</span>
          <span v-else>Reset Password</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { X } from 'lucide-vue-next';
import api from '../../core/api';
import { useNotifications } from '../../composables/useNotifications';

const props = defineProps<{
  isVisible: boolean;
  userId: number;
  userName: string;
  userEmail: string;
}>();

const emit = defineEmits(['close', 'success', 'refresh']);

const { add: showNotification } = useNotifications();

const formData = ref({
  newPassword: '',
  confirmPassword: ''
});

const errors = ref({
  newPassword: '',
  confirmPassword: ''
});

const isLoading = ref(false);

// Password validation
const hasMinLength = computed(() => formData.value.newPassword.length >= 8);
const hasLetter = computed(() => /[A-Za-z]/.test(formData.value.newPassword));
const hasNumber = computed(() => /\d/.test(formData.value.newPassword));

const isPasswordValid = computed(() => 
  hasMinLength.value && hasLetter.value && hasNumber.value
);

const passwordsMatch = computed(() => 
  formData.value.newPassword === formData.value.confirmPassword && 
  formData.value.confirmPassword.length > 0
);

const isFormValid = computed(() => 
  isPasswordValid.value && passwordsMatch.value
);

// Watch for password changes to clear errors
watch(() => formData.value.newPassword, () => {
  errors.value.newPassword = '';
});

watch(() => formData.value.confirmPassword, () => {
  errors.value.confirmPassword = '';
});

const validateForm = () => {
  errors.value = { newPassword: '', confirmPassword: '' };
  let isValid = true;
  
  if (!formData.value.newPassword) {
    errors.value.newPassword = 'New password is required';
    isValid = false;
  } else if (!isPasswordValid.value) {
    errors.value.newPassword = 'Password does not meet requirements';
    isValid = false;
  }
  
  if (!formData.value.confirmPassword) {
    errors.value.confirmPassword = 'Please confirm your password';
    isValid = false;
  } else if (!passwordsMatch.value) {
    errors.value.confirmPassword = 'Passwords do not match';
    isValid = false;
  }
  
  return isValid;
};

const handleSubmit = async () => {
  if (!validateForm()) return;
  
  isLoading.value = true;
  
  try {
    const response = await api.post('/auth/admin/reset-password', {
      user_id: props.userId,
      new_password: formData.value.newPassword,
      confirm_password: formData.value.confirmPassword
    });
    
    showNotification({
      title: 'Success',
      message: response.data.message,
      type: 'success',
      sticky: false
    });
    
    emit('success');
    closeModal();
    
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || 'Failed to reset password';
    showNotification({
      title: 'Error',
      message: errorMessage,
      type: 'danger',
      sticky: false
    });
  } finally {
    isLoading.value = false;
  }
};

const closeModal = () => {
  formData.value = { newPassword: '', confirmPassword: '' };
  errors.value = { newPassword: '', confirmPassword: '' };
  emit('close');
};

const handleOverlayClick = () => {
  if (!isLoading.value) {
    closeModal();
  }
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;
@use "sass:color";

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: v.$overlay-modal;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.2s ease-out;
}

.modal-container {
  background: v.$white;
  border-radius: 8px;
  box-shadow: 0 10px 25px v.$shadow-dark;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideInUp 0.3s ease-out;
  transform-origin: center;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: v.$text-primary;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: v.$text-secondary;
  border-radius: 4px;
  transition: all 0.2s;
  
  &:hover {
    background: #f3f4f6;
    color: v.$text-primary;
  }
}

.modal-body {
  padding: 24px;
}

.user-info {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 24px;
  
  p {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: v.$text-primary;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    strong {
      font-weight: 600;
    }
  }
}

.reset-form {
  .form-group {
    margin-bottom: 20px;
  }
  
  .form-label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: v.$text-primary;
    margin-bottom: 6px;
  }
  
  .form-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 14px;
    transition: all 0.2s;
    
    &:focus {
      outline: none;
      border-color: v.$primary-color;
      box-shadow: 0 0 0 3px rgba(v.$primary-color, 0.1);
    }
    
    &.error {
      border-color: v.$danger-color;
      box-shadow: 0 0 0 3px rgba(v.$danger-color, 0.1);
    }
  }
  
  .error-message {
    color: v.$danger-color;
    font-size: 12px;
    margin-top: 4px;
  }
}

.password-requirements {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 16px;
  margin-top: 16px;
  
  .requirements-title {
    font-size: 14px;
    font-weight: 500;
    color: v.$text-primary;
    margin: 0 0 8px 0;
  }
  
  .requirements-list {
    margin: 0;
    padding-left: 20px;
    
    li {
      font-size: 13px;
      color: v.$text-secondary;
      margin-bottom: 4px;
      
      &.valid {
        color: v.$green-500;
        font-weight: 500;
      }
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 0 0 8px 8px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &.btn-secondary {
    background: v.$white;
    color: v.$text-primary;
    border-color: #d1d5db;
    
    &:hover:not(:disabled) {
      background: #f9fafb;
    }
  }
  
  &.btn-primary {
    background: v.$primary-color;
    color: v.$white;
    
    &:hover:not(:disabled) {
      background: v.$primary-hover;
    }
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

// Dark mode styles
[data-theme="dark"] {
  .modal-container {
    background: #161b22;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }
  
  .modal-header {
    border-bottom-color: #30363d;
  }
  
  .modal-title {
    color: #e6edf3;
  }
  
  .modal-close {
    color: #7d8590;
    
    &:hover {
      background: #21262d;
      color: #e6edf3;
    }
  }
  
  .user-info {
    background: #0d1117;
    border-color: #30363d;
    
    p {
      color: #e6edf3;
    }
  }
  
  .reset-form {
    .form-label {
      color: #e6edf3;
    }
    
    .form-input {
      background: rgba(255, 255, 255, 0.05);
      border-color: #30363d;
      color: #e6edf3;
      
      &::placeholder {
        color: #7d8590;
      }
      
      &:focus {
        border-color: #58a6ff;
        box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1);
      }
      
      &.error {
        border-color: #f85149;
        box-shadow: 0 0 0 3px rgba(248, 81, 73, 0.1);
      }
    }
    
    .error-message {
      color: #f85149;
    }
  }
  
  .password-requirements {
    background: #0d1117;
    border-color: #30363d;
    
    .requirements-title {
      color: #e6edf3;
    }
    
    .requirements-list li {
      color: #7d8590;
      
      &.valid {
        color: #3fb950;
      }
    }
  }
  
  .modal-footer {
    border-top-color: #30363d;
    background: #0d1117;
  }
  
  .btn {
    &.btn-secondary {
      background: #21262d;
      color: #e6edf3;
      border-color: #30363d;
      
      &:hover:not(:disabled) {
        background: #30363d;
      }
    }
    
    &.btn-primary {
      background: #2563eb;
      
      &:hover:not(:disabled) {
        background: #1d4ed8;
      }
    }
  }
}
</style>