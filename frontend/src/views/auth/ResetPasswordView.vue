<template>
  <div class="auth-container">
    <!-- Background Effects -->
    <div class="background-effects">
      <div class="glow-primary"></div>
      <div class="glow-secondary"></div>
      <div class="glow-tertiary"></div>
    </div>

    <!-- Back Button -->
    <div class="back-button">
      <router-link to="/" class="back-link">
        <i class="icofont-arrow-left"></i>
        <span>Back to home</span>
      </router-link>
    </div>

    <!-- Main Content -->
    <main class="auth-main">
      <div class="auth-card">
        <!-- Header -->
        <div class="auth-header">
          <div class="logo-wrapper">
            <img :src="logoImage" alt="Znova" class="logo" />
          </div>
          <h1>Set New Password</h1>
          <p>Enter your new password below</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleResetPassword" v-if="!resetComplete" class="auth-form">
          <!-- New Password -->
          <div class="form-group">
            <label for="password">New Password</label>
            <div class="input-wrapper">
              <i class="icofont-lock"></i>
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter new password"
                required
                :disabled="loading"
                minlength="8"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showPassword = !showPassword"
                :disabled="loading"
                tabindex="-1"
              >
                <svg v-if="showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                  <line x1="1" y1="1" x2="23" y2="23"></line>
                </svg>
              </button>
            </div>
            <div class="password-hint">
              <small>Password must be at least 8 characters long</small>
            </div>
          </div>

          <!-- Confirm Password -->
          <div class="form-group">
            <label for="confirm-password">Confirm New Password</label>
            <div class="input-wrapper">
              <i class="icofont-lock"></i>
              <input
                id="confirm-password"
                v-model="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                placeholder="Confirm new password"
                required
                :disabled="loading"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showConfirmPassword = !showConfirmPassword"
                :disabled="loading"
                tabindex="-1"
              >
                <svg v-if="showConfirmPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                  <line x1="1" y1="1" x2="23" y2="23"></line>
                </svg>
              </button>
            </div>
            <div v-if="confirmPassword && password !== confirmPassword" class="field-error">
              Passwords do not match
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="error-msg">{{ error }}</div>

          <!-- Submit Button -->
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="loading || !isFormValid"
          >
            <span v-if="loading" class="loading-spinner"></span>
            <span v-else>Update Password</span>
            <i v-if="!loading" class="icofont-long-arrow-right"></i>
          </button>
        </form>

        <!-- Success State -->
        <div v-else class="success-state">
          <div class="success-icon">
            <i class="icofont-check-circled"></i>
          </div>
          <h3>Password Updated!</h3>
          <p>Your password has been successfully updated. You can now sign in with your new password.</p>
          <router-link to="/login" class="btn btn-primary">
            Continue to Sign In
            <i class="icofont-long-arrow-right"></i>
          </router-link>
        </div>

        <!-- Footer -->
        <div class="auth-footer" v-if="!resetComplete">
          <p>
            Remember your password?
            <router-link to="/login" class="auth-link">Sign in</router-link>
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import api from '../../core/api';
import logoImage from '@/assets/znova_logo_no_bg.png';

const route = useRoute();

const password = ref('');
const confirmPassword = ref('');
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const loading = ref(false);
const error = ref('');
const resetComplete = ref(false);
const token = ref('');

const isFormValid = computed(() => {
  return password.value.length >= 8 &&
         password.value === confirmPassword.value;
});

onMounted(() => {
  token.value = route.query.token as string || '';
  if (!token.value) {
    error.value = 'Invalid or missing reset token. Please request a new password reset.';
  }
});

const handleResetPassword = async () => {
  if (!isFormValid.value) {
    error.value = 'Please ensure passwords match and are at least 8 characters long';
    return;
  }

  if (!token.value) {
    error.value = 'Invalid reset token. Please request a new password reset.';
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    await api.post('/auth/reset-password', {
      token: token.value,
      new_password: password.value
    });
    resetComplete.value = true;
  } catch (err: any) {
    if (err.response?.status === 400) {
      error.value = 'Invalid or expired reset token. Please request a new password reset.';
    } else {
      error.value = err.response?.data?.detail || 'Failed to reset password. Please try again.';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.auth-container {
  min-height: 100vh;
  background: #0d1117;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.background-effects {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.glow-primary {
  position: absolute;
  top: -10%;
  left: 25%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.2) 0%, transparent 70%);
  filter: blur(120px);
  mix-blend-mode: screen;
  opacity: 0.5;
}

.glow-secondary {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.2) 0%, transparent 70%);
  filter: blur(100px);
  mix-blend-mode: screen;
  opacity: 0.4;
}

.glow-tertiary {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 800px;
  height: 800px;
  background: radial-gradient(circle, rgba(6, 182, 212, 0.05) 0%, transparent 70%);
  filter: blur(90px);
  mix-blend-mode: screen;
  opacity: 0.3;
}

.back-button {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 1.5rem;
  z-index: 20;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: #7d8590;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.3s ease;

  &:hover {
    color: #e6edf3;

    i {
      transform: translateX(-4px);
    }
  }

  i {
    font-size: 1rem;
    transition: transform 0.3s ease;
  }
}

.auth-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  position: relative;
  z-index: 10;
}

.auth-card {
  width: 100%;
  max-width: 450px;
  background: rgba(13, 13, 22, 0.7);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);

  @media (max-width: 480px) {
    padding: 1.5rem;
  }
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;

  .logo {
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 0 15px rgba(37, 99, 235, 0.5));
  }
}

.auth-header h1 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #e6edf3;
  margin-bottom: 0.5rem;
  letter-spacing: -0.02em;
}

.auth-header p {
  color: #7d8590;
  font-size: 0.875rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;

  label {
    font-size: 0.75rem;
    font-weight: 500;
    color: #7d8590;
    margin-left: 0.25rem;
  }
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;

  i {
    position: absolute;
    left: 0.75rem;
    color: #7d8590;
    font-size: 1.125rem;
    pointer-events: none;
  }

  input {
    width: 100%;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    padding: 0.75rem 2.5rem 0.75rem 2.5rem;
    color: #e6edf3;
    font-size: 0.9375rem;
    transition: all 0.3s ease;

    &::placeholder {
      color: #7d8590;
    }

    &:focus {
      outline: none;
      border-color: rgba(37, 99, 235, 0.5);
      box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.5);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    // Override browser autocomplete styling
    &:-webkit-autofill,
    &:-webkit-autofill:hover,
    &:-webkit-autofill:focus,
    &:-webkit-autofill:active {
      -webkit-box-shadow: 0 0 0 30px rgba(255, 255, 255, 0.05) inset !important;
      -webkit-text-fill-color: #e6edf3 !important;
      caret-color: #e6edf3;
      transition: background-color 5000s ease-in-out 0s;
    }
  }
}

.password-toggle {
  position: absolute;
  right: 0.75rem;
  background: none;
  border: none;
  color: #7d8590;
  cursor: pointer;
  padding: 0.25rem;
  transition: color 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover:not(:disabled) {
    color: #e6edf3;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  svg {
    display: block;
  }
}

.password-hint {
  margin-left: 0.25rem;

  small {
    color: #7d8590;
    font-size: 0.75rem;
  }
}

.field-error {
  color: #f85149;
  font-size: 0.75rem;
  margin-left: 0.25rem;
}

.error-msg {
  background: rgba(248, 81, 73, 0.1);
  border: 1px solid rgba(248, 81, 73, 0.2);
  color: #f85149;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
}

.btn {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  text-decoration: none;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &.btn-primary {
    background: #2563eb;
    color: white;
    box-shadow: 0 0 20px rgba(37, 99, 235, 0.3);

    &:hover:not(:disabled) {
      background: #1d4ed8;
      box-shadow: 0 0 30px rgba(37, 99, 235, 0.5);
    }

    i {
      transition: transform 0.3s ease;
    }

    &:hover:not(:disabled) i {
      transform: translateX(4px);
    }
  }
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.success-state {
  text-align: center;
  padding: 1rem 0;

  .success-icon {
    width: 80px;
    height: 80px;
    margin: 0 auto 1.5rem;
    background: rgba(63, 185, 80, 0.1);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;

    i {
      font-size: 2.5rem;
      color: #3fb950;
    }
  }

  h3 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #e6edf3;
    margin-bottom: 1rem;
  }

  p {
    color: #7d8590;
    margin-bottom: 2rem;
    line-height: 1.5;
    font-size: 0.9375rem;
  }
}

.auth-footer {
  margin-top: 1.5rem;
  text-align: center;

  p {
    font-size: 0.875rem;
    color: #7d8590;
  }
}

.auth-link {
  color: #58a6ff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;

  &:hover {
    color: #22d3ee;
  }
}
</style>
