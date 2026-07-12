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
          <h1>Reset Your Password</h1>
          <p>Enter your email address and we'll send you a link to reset your password</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleForgotPassword" v-if="!emailSent" class="auth-form">
          <!-- Email -->
          <div class="form-group">
            <label for="email">Email Address</label>
            <div class="input-wrapper">
              <i class="icofont-email"></i>
              <input
                id="email"
                v-model="email"
                type="email"
                placeholder="john@example.com"
                required
                :disabled="loading"
              />
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="error-msg">{{ error }}</div>

          <!-- Submit Button -->
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="loading || !email.trim()"
          >
            <span v-if="loading" class="loading-spinner"></span>
            <span v-else>Send Reset Link</span>
            <i v-if="!loading" class="icofont-long-arrow-right"></i>
          </button>
        </form>

        <!-- Success State -->
        <div v-else class="success-state">
          <div class="success-icon">
            <i class="icofont-email"></i>
          </div>
          <h3>Check Your Email</h3>
          <p>We've sent a password reset link to <strong>{{ email }}</strong></p>
          <p class="help-text">
            Didn't receive the email? Check your spam folder or
            <button @click="handleResend" class="resend-btn" :disabled="resendCooldown > 0">
              {{ resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'click here to resend' }}
            </button>
          </p>
        </div>

        <!-- Footer -->
        <div class="auth-footer">
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
import { ref, onUnmounted } from 'vue';
import api from '../../core/api';
import logoImage from '@/assets/znova_logo_no_bg.png';

const email = ref('');
const loading = ref(false);
const error = ref('');
const emailSent = ref(false);
const resendCooldown = ref(0);

let resendTimer: ReturnType<typeof setInterval> | null = null;

const handleForgotPassword = async () => {
  loading.value = true;
  error.value = '';

  try {
    await api.post('/auth/forgot-password', { email: email.value });
    emailSent.value = true;
    startResendCooldown();
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to send reset email. Please try again.';
  } finally {
    loading.value = false;
  }
};

const handleResend = async () => {
  if (resendCooldown.value > 0) return;

  loading.value = true;
  error.value = '';

  try {
    await api.post('/auth/forgot-password', { email: email.value });
    startResendCooldown();
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to resend email. Please try again.';
  } finally {
    loading.value = false;
  }
};

const startResendCooldown = () => {
  resendCooldown.value = 60;
  resendTimer = setInterval(() => {
    resendCooldown.value--;
    if (resendCooldown.value <= 0 && resendTimer) {
      clearInterval(resendTimer);
      resendTimer = null;
    }
  }, 1000);
};

onUnmounted(() => {
  if (resendTimer) {
    clearInterval(resendTimer);
  }
});
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
  line-height: 1.5;
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
    padding: 0.75rem 1rem 0.75rem 2.5rem;
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
    background: rgba(37, 99, 235, 0.1);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;

    i {
      font-size: 2.5rem;
      color: #58a6ff;
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
    margin-bottom: 1rem;
    line-height: 1.5;
    font-size: 0.9375rem;

    strong {
      color: #e6edf3;
    }
  }

  .help-text {
    font-size: 0.875rem;

    .resend-btn {
      background: none;
      border: none;
      color: #58a6ff;
      cursor: pointer;
      text-decoration: underline;
      font-size: inherit;
      transition: color 0.3s ease;

      &:hover:not(:disabled) {
        color: #22d3ee;
      }

      &:disabled {
        color: #7d8590;
        cursor: not-allowed;
        text-decoration: none;
      }
    }
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
