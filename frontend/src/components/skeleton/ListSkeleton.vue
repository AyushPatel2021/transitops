<template>
  <div class="list-skeleton" :style="containerStyle">
    <!-- Header Skeleton -->
    <div class="skeleton-list-header" :style="headerStyle">
      <div class="skeleton-header-left">
        <div class="skeleton-breadcrumb" :style="{ background: shimmerStyle, backgroundSize: '200% 100%' }"></div>
        <div class="skeleton-title" :style="{ background: shimmerStyle, backgroundSize: '200% 100%' }"></div>
      </div>
      <div class="skeleton-header-actions">
        <div class="skeleton-search-box" :style="{ background: cellShimmerStyle, backgroundSize: '200% 100%', border: isDark ? '1px solid #30363d' : '1px solid #E5E7EB' }"></div>
        <div class="skeleton-action-btn primary" :style="{ background: isDark ? 'linear-gradient(90deg, #1c3d5a 25%, #2563eb 50%, #1c3d5a 75%)' : 'linear-gradient(90deg, #DBEAFE 25%, #BFDBFE 50%, #DBEAFE 75%)', backgroundSize: '200% 100%' }"></div>
      </div>
    </div>
    
    <!-- Filters/Toolbar Skeleton -->
    <div class="skeleton-toolbar" :style="{ background: isDark ? '#161b22' : 'white', borderBottom: isDark ? '1px solid #30363d' : '1px solid #E5E7EB' }">
      <div class="skeleton-filter-group">
        <div class="skeleton-filter" v-for="n in 3" :key="n" :style="{ background: cellShimmerStyle, backgroundSize: '200% 100%', border: isDark ? '1px solid #30363d' : '1px solid #E5E7EB' }"></div>
      </div>
      <div class="skeleton-view-controls">
        <div class="skeleton-view-btn" v-for="n in 2" :key="n" :style="{ background: cellShimmerStyle, backgroundSize: '200% 100%', border: isDark ? '1px solid #30363d' : '1px solid #E5E7EB' }"></div>
      </div>
    </div>
    
    <!-- Table Header Skeleton -->
    <div class="skeleton-table">
      <div class="skeleton-table-header" :style="{ background: isDark ? '#0d1117' : '#F9FAFB', borderBottom: isDark ? '2px solid #30363d' : '2px solid #E5E7EB' }">
        <div class="skeleton-checkbox" :style="{ background: cellShimmerStyle, backgroundSize: '200% 100%', border: isDark ? '1px solid #30363d' : '1px solid #E5E7EB' }"></div>
        <div 
          v-for="n in columnCount" 
          :key="n" 
          class="skeleton-column-header"
          :style="{ width: getColumnWidth(n), background: shimmerStyle, backgroundSize: '200% 100%' }"
        ></div>
        <div class="skeleton-actions-header" :style="{ background: shimmerStyle, backgroundSize: '200% 100%' }"></div>
      </div>
      
      <!-- Table Rows Skeleton -->
      <div class="skeleton-table-body" :style="{ background: isDark ? '#161b22' : 'white' }">
        <div 
          v-for="n in rowCount" 
          :key="n" 
          class="skeleton-table-row"
          :style="{ borderBottom: isDark ? '1px solid #21262d' : '1px solid #F3F4F6' }"
        >
          <div class="skeleton-checkbox" :style="{ background: cellShimmerStyle, backgroundSize: '200% 100%', border: isDark ? '1px solid #30363d' : '1px solid #E5E7EB' }"></div>
          <div 
            v-for="col in columnCount" 
            :key="col" 
            class="skeleton-table-cell"
            :style="{ width: getColumnWidth(col), background: cellShimmerStyle, backgroundSize: '200% 100%' }"
          ></div>
          <div class="skeleton-row-actions">
            <div class="skeleton-action-dot" v-for="dot in 3" :key="dot" :style="{ background: shimmerStyle, backgroundSize: '200% 100%' }"></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Pagination Skeleton -->
    <div class="skeleton-pagination" :style="{ background: isDark ? '#0d1117' : '#FAFAFA', borderTop: isDark ? '1px solid #30363d' : '1px solid #E5E7EB' }">
      <div class="skeleton-pagination-info" :style="{ background: cellShimmerStyle, backgroundSize: '200% 100%' }"></div>
      <div class="skeleton-pagination-controls">
        <div class="skeleton-page-btn" v-for="n in 5" :key="n" :style="{ background: cellShimmerStyle, backgroundSize: '200% 100%', border: isDark ? '1px solid #30363d' : '1px solid #E5E7EB' }"></div>
      </div>
    </div>
  </div>
</template>
    <!-- Header Skeleton -->
    <div class="skeleton-list-header">
      <div class="skeleton-header-left">
        <div class="skeleton-breadcrumb"></div>
        <div class="skeleton-title"></div>
      </div>
      <div class="skeleton-header-actions">
        <div class="skeleton-search-box"></div>
        <div class="skeleton-action-btn primary"></div>
      </div>
    </div>
    
    <!-- Filters/Toolbar Skeleton -->
    <div class="skeleton-toolbar">
      <div class="skeleton-filter-group">
        <div class="skeleton-filter" v-for="n in 3" :key="n"></div>
      </div>
      <div class="skeleton-view-controls">
        <div class="skeleton-view-btn" v-for="n in 2" :key="n"></div>
      </div>
    </div>
    
    <!-- Table Header Skeleton -->
    <div class="skeleton-table">
      <div class="skeleton-table-header">
        <div class="skeleton-checkbox"></div>
        <div 
          v-for="n in columnCount" 
          :key="n" 
          class="skeleton-column-header"
          :style="{ width: getColumnWidth(n) }"
        ></div>
        <div class="skeleton-actions-header"></div>
      </div>
      
      <!-- Table Rows Skeleton -->
      <div class="skeleton-table-body">
        <div 
          v-for="n in rowCount" 
          :key="n" 
          class="skeleton-table-row"
        >
          <div class="skeleton-checkbox"></div>
          <div 
            v-for="col in columnCount" 
            :key="col" 
            class="skeleton-table-cell"
            :style="{ width: getColumnWidth(col) }"
          ></div>
          <div class="skeleton-row-actions">
            <div class="skeleton-action-dot" v-for="dot in 3" :key="dot"></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Pagination Skeleton -->
    <div class="skeleton-pagination">
      <div class="skeleton-pagination-info"></div>
      <div class="skeleton-pagination-controls">
        <div class="skeleton-page-btn" v-for="n in 5" :key="n"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

interface Props {
  rowCount?: number;
  columnCount?: number;
}

const props = withDefaults(defineProps<Props>(), {
  rowCount: 8,
  columnCount: 5
});

const getColumnWidth = (index: number) => {
  const widths = ['15%', '25%', '20%', '15%', '25%'];
  return widths[index - 1] || '20%';
};

// Reactive dark mode detection
const isDark = ref(false);

const updateTheme = () => {
  isDark.value = document.documentElement.getAttribute('data-theme') === 'dark';
};

onMounted(() => {
  updateTheme();
  // Watch for theme changes
  const observer = new MutationObserver(updateTheme);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  });
});

// Dynamic styles based on theme
const containerStyle = computed(() => ({
  background: isDark.value ? '#161b22' : 'white',
  border: isDark.value ? '1px solid #30363d' : '1px solid #E5E7EB'
}));

const headerStyle = computed(() => ({
  background: isDark.value ? '#0d1117' : '#FAFAFA',
  borderBottom: isDark.value ? '1px solid #30363d' : '1px solid #E5E7EB'
}));

const shimmerStyle = computed(() => 
  isDark.value 
    ? 'linear-gradient(90deg, #30363d 25%, #21262d 50%, #30363d 75%)'
    : 'linear-gradient(90deg, #9CA3AF 25%, #F9FAFB 50%, #9CA3AF 75%)'
);

const cellShimmerStyle = computed(() => 
  isDark.value 
    ? 'linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%)'
    : 'linear-gradient(90deg, #D1D5DB 25%, #F9FAFB 50%, #D1D5DB 75%)'
);
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.list-skeleton {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.skeleton-list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
}

.skeleton-header-left {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-breadcrumb {
  width: 250px;
  height: 14px;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-title {
  width: 200px;
  height: 32px;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}

.skeleton-header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.skeleton-search-box {
  width: 300px;
  height: 40px;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}

.skeleton-action-btn {
  width: 120px;
  height: 40px;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}

.skeleton-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
}

.skeleton-filter-group {
  display: flex;
  gap: 1rem;
}

.skeleton-filter {
  width: 120px;
  height: 36px;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}

.skeleton-view-controls {
  display: flex;
  gap: 0.5rem;
}

.skeleton-view-btn {
  width: 36px;
  height: 36px;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}

.skeleton-table {
  overflow: hidden;
}

.skeleton-table-header {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  gap: 1rem;
}

.skeleton-checkbox {
  width: 16px;
  height: 16px;
  animation: shimmer 1.5s infinite;
  border-radius: 3px;
  flex-shrink: 0;
}

.skeleton-column-header {
  height: 20px;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-actions-header {
  width: 60px;
  height: 20px;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  flex-shrink: 0;
}

.skeleton-table-row {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  gap: 1rem;
}

.skeleton-table-cell {
  height: 16px;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-row-actions {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
  width: 60px;
  justify-content: center;
}

.skeleton-action-dot {
  width: 4px;
  height: 4px;
  animation: shimmer 1.5s infinite;
  border-radius: 50%;
}

.skeleton-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
}

.skeleton-pagination-info {
  width: 150px;
  height: 16px;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-pagination-controls {
  display: flex;
  gap: 0.5rem;
}

.skeleton-page-btn {
  width: 32px;
  height: 32px;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@media (max-width: 1024px) {
  .skeleton-list-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  .skeleton-header-actions {
    flex-direction: column;
    gap: 0.75rem;
  }
  .skeleton-search-box { width: 100%; }
  .skeleton-toolbar {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  .skeleton-filter-group { flex-wrap: wrap; }
  .skeleton-table-header, .skeleton-table-row { padding: 0.75rem 1rem; }
  .skeleton-pagination {
    flex-direction: column;
    gap: 1rem;
    align-items: center;
  }
}

@media (max-width: 768px) {
  .skeleton-list-header { padding: 1rem; }
  .skeleton-toolbar { padding: 0.75rem 1rem; }
  .skeleton-table-header, .skeleton-table-row {
    padding: 0.5rem 1rem;
    gap: 0.5rem;
  }
  .skeleton-column-header, .skeleton-table-cell { min-width: 60px; }
  .skeleton-pagination { padding: 0.75rem 1rem; }
}
</style>
