<template>
  <div class="form-skeleton-debug">
    <div class="debug-info">🔍 SKELETON DEBUG MODE</div>
    
    <!-- Header Skeleton -->
    <div class="skeleton-form-header">
      <div class="skeleton-header-content">
        <div class="skeleton-breadcrumb"></div>
        <div class="skeleton-title-section">
          <div class="skeleton-model-label"></div>
          <div class="skeleton-title"></div>
        </div>
      </div>
      <div class="skeleton-header-actions">
        <div class="skeleton-action-btn"></div>
        <div class="skeleton-action-btn primary"></div>
      </div>
    </div>
    
    <!-- Form Content Skeleton -->
    <div class="skeleton-form-content">
      <!-- Left Column -->
      <div class="skeleton-form-column">
        <div class="skeleton-form-group">
          <div class="skeleton-group-title"></div>
          <div class="skeleton-fields">
            <div class="skeleton-field">
              <div class="skeleton-field-label"></div>
              <div class="skeleton-field-input"></div>
            </div>
            <div class="skeleton-field">
              <div class="skeleton-field-label"></div>
              <div class="skeleton-field-input"></div>
            </div>
            <div class="skeleton-field">
              <div class="skeleton-field-label"></div>
              <div class="skeleton-field-input textarea"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Right Column -->
      <div class="skeleton-form-column">
        <div class="skeleton-form-group">
          <div class="skeleton-group-title"></div>
          <div class="skeleton-fields">
            <div class="skeleton-field">
              <div class="skeleton-field-label"></div>
              <div class="skeleton-field-input"></div>
            </div>
            <div class="skeleton-field">
              <div class="skeleton-field-label"></div>
              <div class="skeleton-field-input"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Debug version with no props - just shows the skeleton
</script>

<style scoped>
.form-skeleton-debug {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #DC2626; /* Red border to make it obvious */
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin: 20px;
}

.debug-info {
  background: #DC2626;
  color: white;
  padding: 10px;
  text-align: center;
  font-weight: bold;
  font-size: 14px;
}

.skeleton-form-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  border-bottom: 1px solid #E5E7EB;
  gap: 2rem;
  background: #FAFAFA;
}

.skeleton-header-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.skeleton-breadcrumb {
  width: 300px;
  height: 16px;
  background: linear-gradient(90deg, #9CA3AF 25%, #F9FAFB 50%, #9CA3AF 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-title-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-model-label {
  width: 100px;
  height: 14px;
  background: linear-gradient(90deg, #9CA3AF 25%, #F9FAFB 50%, #9CA3AF 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-title {
  width: 400px;
  height: 40px;
  background: linear-gradient(90deg, #9CA3AF 25%, #F9FAFB 50%, #9CA3AF 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}

.skeleton-header-actions {
  display: flex;
  gap: 0.75rem;
  flex-shrink: 0;
}

.skeleton-action-btn {
  width: 80px;
  height: 36px;
  background: linear-gradient(90deg, #D1D5DB 25%, #F9FAFB 50%, #D1D5DB 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
}

.skeleton-action-btn.primary {
  width: 100px;
  background: linear-gradient(90deg, #DBEAFE 25%, #BFDBFE 50%, #DBEAFE 75%);
  background-size: 200% 100%;
}

.skeleton-form-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  padding: 2rem;
}

.skeleton-form-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.skeleton-form-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.skeleton-group-title {
  width: 150px;
  height: 20px;
  background: linear-gradient(90deg, #9CA3AF 25%, #F9FAFB 50%, #9CA3AF 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-fields {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.skeleton-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-field-label {
  width: 120px;
  height: 16px;
  background: linear-gradient(90deg, #D1D5DB 25%, #F9FAFB 50%, #D1D5DB 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-field-input {
  height: 40px;
  background: linear-gradient(90deg, #D1D5DB 25%, #F9FAFB 50%, #D1D5DB 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
}

.skeleton-field-input.textarea {
  height: 80px;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* Mobile responsive */
@media (max-width: 1024px) {
  .skeleton-form-content {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .skeleton-form-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
}
</style>