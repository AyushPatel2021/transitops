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
          <h1>Sign In</h1>
          <p>Welcome back to Znova framework.</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="auth-form">
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

          <!-- Password -->
          <div class="form-group">
            <label for="password">Password</label>
            <div class="input-wrapper">
              <i class="icofont-lock"></i>
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                required
                :disabled="loading"
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
          </div>

          <!-- Remember Me & Forgot Password -->
          <div class="form-options">
            <label class="checkbox-label">
              <input type="checkbox" v-model="rememberMe" :disabled="loading" />
              <span>Remember me</span>
            </label>
            <router-link to="/forgot-password" class="forgot-link">
              Forgot password?
            </router-link>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="error-msg">{{ error }}</div>

          <!-- Submit Button -->
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="loading"
          >
            <span v-if="loading" class="loading-spinner"></span>
            <span v-else>Sign In</span>
            <i v-if="!loading" class="icofont-long-arrow-right"></i>
          </button>

          <!-- Divider -->
          <div class="divider">
            <span>Or</span>
          </div>

          <!-- Google Button -->
          <button
            type="button"
            @click="handleGoogleLogin"
            class="btn btn-google"
            :disabled="loading"
          >
            <svg class="google-icon" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>
        </form>

        <!-- Footer -->
        <div class="auth-footer">
          <p>
            Don't have an account?
            <router-link to="/signup" class="auth-link">Create one</router-link>
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../../core/useAuth';
import api from '../../core/api';
import logoImage from '@/assets/znova_logo_no_bg.png';

const router = useRouter();
const { login } = useAuth();

const email = ref('');
const password = ref('');
const rememberMe = ref(false);
const showPassword = ref(false);
const loading = ref(false);
const error = ref('');

// Load saved email if remember me was checked
const savedEmail = localStorage.getItem('rememberedEmail');
if (savedEmail) {
  email.value = savedEmail;
  rememberMe.value = true;
}

const handleLogin = async () => {
  if (!email.value || !password.value) {
    error.value = 'Please enter both email and password';
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    await login(email.value, password.value);
    
    // Handle remember me
    if (rememberMe.value) {
      localStorage.setItem('rememberedEmail', email.value);
    } else {
      localStorage.removeItem('rememberedEmail');
    }
    
    // Redirect immediately without success message
    router.push('/dashboard');
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Login failed. Please check your credentials.';
    loading.value = false;
  }
};

const handleGoogleLogin = async () => {
  loading.value = true;
  error.value = '';

  try {
    const response = await api.get('/auth/google');
    const { auth_url, state } = response.data;
    localStorage.setItem('google_oauth_state', state);
    window.location.href = auth_url;
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Google login failed. Please try again.';
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

// Background Effects
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

// Back Button
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

// Main Content
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

// Header
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

// Form
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

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.25rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: #7d8590;
  transition: color 0.3s ease;
  
  &:hover {
    color: #e6edf3;
  }
  
  input[type="checkbox"] {
    width: 16px;
    height: 16px;
    border-radius: 0.25rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    cursor: pointer;
    
    &:checked {
      background: #2563eb;
      border-color: #2563eb;
    }
    
    &:focus {
      outline: none;
      box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.5);
    }
  }
}

.forgot-link {
  font-size: 0.875rem;
  color: #58a6ff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
  
  &:hover {
    color: #22d3ee;
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

// Buttons
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
  
  &.btn-google {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #e6edf3;
    
    &:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.1);
    }
  }
}

.google-icon {
  width: 20px;
  height: 20px;
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

// Divider
.divider {
  position: relative;
  display: flex;
  align-items: center;
  text-align: center;
  margin: 0.25rem 0;
  
  &::before,
  &::after {
    content: '';
    flex: 1;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  span {
    padding: 0 1rem;
    color: #7d8590;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
}

// Footer
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
