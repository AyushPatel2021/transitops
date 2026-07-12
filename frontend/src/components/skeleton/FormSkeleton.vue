<template>
  <div class="form-skeleton-content">
    <!-- Status Bar Skeleton -->
    <div class="skeleton-status-bar">
      <div class="skeleton-status-left">
        <div class="skeleton-btn"></div>
        <div class="skeleton-btn"></div>
      </div>
      
      <div class="skeleton-status-center">
        <div class="skeleton-smart-btn"></div>
        <div class="skeleton-smart-btn"></div>
        <div class="skeleton-smart-btn"></div>
      </div>
      
      <div class="skeleton-status-right">
        <div class="skeleton-status-badges">
          <div class="skeleton-badge"></div>
          <div class="skeleton-badge"></div>
          <div class="skeleton-badge"></div>
        </div>
      </div>
    </div>

    <!-- Header Skeleton -->
    <div class="skeleton-sheet-header">
      <div class="skeleton-title-section">
        <div class="skeleton-model-label"></div>
        <div class="skeleton-title"></div>
      </div>
    </div>
    
    <!-- Form Fields Skeleton -->
    <div class="skeleton-form-grid">
      <!-- Left Column -->
      <div class="skeleton-form-column">
        <div v-for="n in leftFieldCount" :key="`left-${n}`" class="skeleton-field">
          <div class="skeleton-field-label"></div>
          <div class="skeleton-field-input"></div>
        </div>
      </div>
      
      <!-- Right Column -->
      <div class="skeleton-form-column">
        <div v-for="n in rightFieldCount" :key="`right-${n}`" class="skeleton-field">
          <div class="skeleton-field-label"></div>
          <div class="skeleton-field-input"></div>
        </div>
      </div>
    </div>
    
    <!-- Tabs Skeleton -->
    <div v-if="showTabs" class="skeleton-tabs">
      <div class="skeleton-tab-headers">
        <div v-for="n in 4" :key="`tab-${n}`" class="skeleton-tab-header"></div>
      </div>
      <div class="skeleton-tab-content">
        <div v-for="n in tabFieldCount" :key="`tab-field-${n}`" class="skeleton-field">
          <div class="skeleton-field-label"></div>
          <div class="skeleton-field-input small"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  leftFieldCount?: number;
  rightFieldCount?: number;
  tabFieldCount?: number;
  showTabs?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  leftFieldCount: 4,
  rightFieldCount: 4,
  tabFieldCount: 2,
  showTabs: true
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.form-skeleton-content {
  width: 100%;
}

/* Status Bar Skeleton - matches the actual status bar position */
.skeleton-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  border-bottom: 1px solid v.$border-color;
  margin: -1rem -2rem 2rem -2rem;
  padding: 0 2rem;
  background: #FAFAFA;
  gap: 1.5rem;
}

.skeleton-status-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.skeleton-status-center {
  display: flex;
  gap: 12px;
  align-items: center;
  flex: 1;
  justify-content: center;
}

.skeleton-status-right {
  display: flex;
  align-items: center;
}

.skeleton-btn {
  width: 80px;
  height: 36px;
  background: linear-gradient(90deg, #E5E7EB 25%, #F3F4F6 50%, #E5E7EB 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 6px;
}

.skeleton-smart-btn {
  width: 100px;
  height: 40px;
  background: linear-gradient(90deg, #F3F4F6 25%, #FFFFFF 50%, #F3F4F6 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 8px;
  border: 1px solid #E5E7EB;
}

.skeleton-status-badges {
  display: flex;
  gap: 8px;
}

.skeleton-badge {
  width: 90px;
  height: 32px;
  background: linear-gradient(90deg, #E5E7EB 25%, #F3F4F6 50%, #E5E7EB 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 16px;
}

.skeleton-sheet-header {
  margin-bottom: 2rem;
}

.skeleton-model-label {
  width: 100px;
  height: 12px;
  background: linear-gradient(90deg, #E5E7EB 25%, #F9FAFB 50%, #E5E7EB 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.skeleton-title {
  width: 60%;
  height: 40px;
  background: linear-gradient(90deg, #E5E7EB 25%, #F9FAFB 50%, #E5E7EB 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 8px;
}

.skeleton-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.skeleton-form-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.skeleton-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-field-label {
  width: 120px;
  height: 14px;
  background: linear-gradient(90deg, #F3F4F6 25%, #FFFFFF 50%, #F3F4F6 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
}

.skeleton-field-input {
  height: 36px;
  background: linear-gradient(90deg, #F9FAFB 25%, #FFFFFF 50%, #F9FAFB 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
}

.skeleton-field-input.small {
  height: 32px;
}

.skeleton-tabs {
  margin-top: 2rem;
  padding-top: 0;
}

.skeleton-tab-headers {
  display: flex;
  border-bottom: 1px solid #E5E7EB;
  margin-bottom: 1.5rem;
  gap: 0;
}

.skeleton-tab-header {
  width: 120px;
  height: 40px;
  background: linear-gradient(90deg, #F3F4F6 25%, #FFFFFF 50%, #F3F4F6 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  margin-bottom: 0;
  border-bottom: none;
}

.skeleton-tab-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem 0;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

// Dark Mode Styles
[data-theme="dark"] {
  .skeleton-status-bar {
    background: #161b22;
    border-bottom: 1px solid #30363d;
  }

  .skeleton-btn {
    background: linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%);
    background-size: 200% 100%;
  }

  .skeleton-smart-btn {
    background: linear-gradient(90deg, #161b22 25%, #21262d 50%, #161b22 75%);
    background-size: 200% 100%;
    border: 1px solid #30363d;
  }

  .skeleton-badge {
    background: linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%);
    background-size: 200% 100%;
  }

  .skeleton-model-label {
    background: linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%);
    background-size: 200% 100%;
  }

  .skeleton-title {
    background: linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%);
    background-size: 200% 100%;
  }

  .skeleton-field-label {
    background: linear-gradient(90deg, #161b22 25%, #21262d 50%, #161b22 75%);
    background-size: 200% 100%;
  }

  .skeleton-field-input {
    background: linear-gradient(90deg, #0d1117 25%, #161b22 50%, #0d1117 75%);
    background-size: 200% 100%;
  }

  .skeleton-tab-headers {
    border-bottom: 1px solid #30363d;
  }

  .skeleton-tab-header {
    background: linear-gradient(90deg, #161b22 25%, #21262d 50%, #161b22 75%);
    background-size: 200% 100%;
  }
}

@media (max-width: 1024px) {
  .skeleton-form-grid { 
    grid-template-columns: 1fr; 
  }
  
  .skeleton-status-bar { 
    margin: -1rem -1rem 1.5rem -1rem;
    padding: 0 1rem;
    height: 48px;
  }
  
  .skeleton-status-center {
    display: none;
  }
  
  .skeleton-status-right {
    .skeleton-status-badges {
      gap: 4px;
      
      .skeleton-badge {
        width: 70px;
        height: 28px;
      }
    }
  }
}
</style>