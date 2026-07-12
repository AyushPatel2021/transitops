<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1 class="error-title">Page Not Found</h1>
      <p class="error-message">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div class="error-actions">
        <button @click="goHome" class="btn btn-primary">
          <Home class="icon-sm" />
          <span>Go to Dashboard</span>
        </button>
        <button @click="goBack" class="btn btn-secondary">
          <ArrowLeft class="icon-sm" />
          <span>Go Back</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { Home, ArrowLeft } from 'lucide-vue-next';

const router = useRouter();

const goHome = () => {
  router.push('/dashboard');
};

const goBack = () => {
  router.back();
};
</script>

<style lang="scss" scoped>
@use "../styles/variables" as v;

.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: v.$bg-main;
  padding: 2rem;
}

.not-found-content {
  text-align: center;
  max-width: 500px;
}

.error-code {
  font-size: 8rem;
  font-weight: 700;
  color: v.$primary-color;
  line-height: 1;
  margin-bottom: 1rem;
  
  @media (max-width: 768px) {
    font-size: 6rem;
  }
}

.error-title {
  font-size: 2rem;
  font-weight: 600;
  color: v.$text-primary;
  margin-bottom: 1rem;
  
  @media (max-width: 768px) {
    font-size: 1.5rem;
  }
}

.error-message {
  font-size: 1.125rem;
  color: v.$text-secondary;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  
  .btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    border-radius: v.$radius-btn;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    
    .icon-sm {
      width: 18px;
      height: 18px;
    }
  }
  
  .btn-primary {
    background: v.$primary-color;
    color: v.$white;
    
    &:hover {
      background: v.$primary-hover;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(v.$primary-color, 0.3);
    }
  }
  
  .btn-secondary {
    background: v.$white;
    color: v.$text-primary;
    border: 1px solid v.$border-color;
    
    &:hover {
      background: v.$border-light;
      transform: translateY(-1px);
    }
  }
}

// Dark mode
[data-theme="dark"] {
  .not-found-container {
    background: #0d1117;
  }
  
  .error-code {
    color: #2563eb;
  }
  
  .error-title {
    color: #e6edf3;
  }
  
  .error-message {
    color: #7d8590;
  }
  
  .btn-secondary {
    background: #161b22;
    color: #e6edf3;
    border-color: #30363d;
    
    &:hover {
      background: #1c2128;
    }
  }
}
</style>
