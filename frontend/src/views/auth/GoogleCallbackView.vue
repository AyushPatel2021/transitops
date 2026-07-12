<template>
  <div class="auth-container">
    <!-- Background Effects -->
    <div class="background-effects">
      <div class="glow-primary"></div>
      <div class="glow-secondary"></div>
      <div class="glow-tertiary"></div>
    </div>

    <!-- Main Content -->
    <main class="auth-main">
      <div class="auth-card">
        <!-- Header -->
        <div class="auth-header">
          <div class="logo-wrapper">
            <img :src="logoImage" alt="Znova" class="logo" />
          </div>
          <h1>Completing Google Sign In</h1>
          <p>Please wait while we process your authentication...</p>
        </div>

        <!-- Loading State -->
        <div class="loading-state" v-if="!error">
          <div class="loading-spinner large"></div>
          <p>{{ statusMessage }}</p>
        </div>

        <!-- Error State -->
        <div v-if="error" class="error-state">
          <div class="error-icon">
            <i class="icofont-warning"></i>
          </div>
          <div class="error-msg">{{ error }}</div>
          <router-link to="/login" class="btn btn-primary">
            Back to Login
            <i class="icofont-long-arrow-right"></i>
          </router-link>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '../../core/useAuth';
import api from '../../core/api';
import logoImage from '@/assets/znova_logo_no_bg.png';

const route = useRoute();
const router = useRouter();
const { setToken, setUser } = useAuth();

const statusMessage = ref('Processing Google authentication...');
const error = ref('');

onMounted(async () => {
  try {
    const code = route.query.code as string;
    const state = route.query.state as string;
    const storedState = localStorage.getItem('google_oauth_state');

    // Validate state parameter
    if (!state || !storedState || state !== storedState) {
      throw new Error('Invalid state parameter. Possible CSRF attack.');
    }

    // Clear stored state
    localStorage.removeItem('google_oauth_state');

    if (!code) {
      throw new Error('Authorization code not received from Google.');
    }

    statusMessage.value = 'Exchanging authorization code...';

    // Send code to backend
    const response = await api.post('/auth/google', {
      code: code,
      state: state
    });

    const { access_token, user } = response.data;

    statusMessage.value = 'Login successful! Redirecting...';

    // Set authentication data
    setToken(access_token);
    setUser(user);

    // Redirect to dashboard
    setTimeout(() => {
      router.push('/dashboard');
    }, 1000);

  } catch (err: any) {
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail;
    } else if (err.message) {
      error.value = err.message;
    } else {
      error.value = 'Google authentication failed. Please try again.';
    }
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
  text-align: center;

  @media (max-width: 480px) {
    padding: 1.5rem;
  }
}

.auth-header {
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

.loading-state {
  padding: 2rem 0;

  p {
    margin-top: 1.5rem;
    color: #7d8590;
    font-size: 0.9375rem;
  }
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top: 3px solid #58a6ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;

  &.large {
    width: 48px;
    height: 48px;
    border-width: 4px;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-state {
  padding: 1rem 0;
}

.error-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: rgba(248, 81, 73, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;

  i {
    font-size: 2.5rem;
    color: #f85149;
  }
}

.error-msg {
  background: rgba(248, 81, 73, 0.1);
  border: 1px solid rgba(248, 81, 73, 0.2);
  color: #f85149;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
  line-height: 1.5;
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

  &.btn-primary {
    background: #2563eb;
    color: white;
    box-shadow: 0 0 20px rgba(37, 99, 235, 0.3);

    &:hover {
      background: #1d4ed8;
      box-shadow: 0 0 30px rgba(37, 99, 235, 0.5);
    }

    i {
      transition: transform 0.3s ease;
    }

    &:hover i {
      transform: translateX(4px);
    }
  }
}
</style>
