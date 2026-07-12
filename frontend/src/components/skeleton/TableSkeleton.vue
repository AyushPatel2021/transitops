<template>
  <div class="table-skeleton-bare">
    <!-- Table Body Skeleton -->
    <div v-if="part === 'table'" class="skeleton-table-body">
      <!-- Table Header Skeleton -->
      <div class="skeleton-table-header">
        <div class="skeleton-checkbox"></div>
        <div 
          v-for="n in columnCount" 
          :key="n" 
          class="skeleton-column-header"
          :style="{ width: getColumnWidth(n) }"
        ></div>
      </div>
      
      <!-- Table Rows Skeleton -->
      <div class="skeleton-rows">
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
        </div>
      </div>
    </div>

    <!-- Pagination Footer Skeleton -->
    <div v-else-if="part === 'pager'" class="skeleton-pagination-content">
      <div class="skeleton-pagination-info"></div>
      <div class="skeleton-pagination-controls">
        <div class="skeleton-page-btn" v-for="n in 3" :key="n"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  rowCount?: number;
  columnCount?: number;
  part?: 'table' | 'pager';
}

const props = withDefaults(defineProps<Props>(), {
  rowCount: 8,
  columnCount: 5,
  part: 'table'
});

const getColumnWidth = (index: number) => {
  const widths = ['20%', '25%', '15%', '15%', '20%'];
  return widths[index - 1] || '20%';
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.table-skeleton-bare {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.skeleton-table-header {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  border-bottom: 2px solid v.$bg-main;
  background: #FAFAFA;
  gap: 1.5rem;
  height: 44px;
}

.skeleton-checkbox {
  width: 16px;
  height: 16px;
  background: linear-gradient(90deg, #F3F4F6 25%, #FFFFFF 50%, #F3F4F6 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
  border: 1px solid v.$border-color;
  flex-shrink: 0;
}

.skeleton-column-header {
  height: 14px;
  background: linear-gradient(90deg, #E5E7EB 25%, #F9FAFB 50%, #E5E7EB 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
}

.skeleton-rows {
  flex: 1;
}

.skeleton-table-row {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid v.$bg-main;
  gap: 1.5rem;
  height: 52px;
}

.skeleton-table-cell {
  height: 12px;
  background: linear-gradient(90deg, #F3F4F6 25%, #FFFFFF 50%, #F3F4F6 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 3px;
}

/* Pagination Content */
.skeleton-pagination-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.skeleton-pagination-info {
  width: 180px;
  height: 14px;
  background: linear-gradient(90deg, #F3F4F6 25%, #FFFFFF 50%, #F3F4F6 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
}

.skeleton-pagination-controls {
  display: flex;
  gap: 8px;
}

.skeleton-page-btn {
  width: 32px;
  height: 32px;
  background: linear-gradient(90deg, #F3F4F6 25%, #FFFFFF 50%, #F3F4F6 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 8px;
  border: 1px solid v.$border-color;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

// Dark Mode Styles
[data-theme="dark"] {
  .skeleton-table-header {
    background: #0d1117;
    border-bottom: 2px solid #30363d;
  }

  .skeleton-checkbox {
    background: linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%);
    background-size: 200% 100%;
    border: 1px solid #30363d;
  }

  .skeleton-column-header {
    background: linear-gradient(90deg, #30363d 25%, #21262d 50%, #30363d 75%);
    background-size: 200% 100%;
  }

  .skeleton-table-row {
    border-bottom: 1px solid #21262d;
  }

  .skeleton-table-cell {
    background: linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%);
    background-size: 200% 100%;
  }

  .skeleton-pagination-info {
    background: linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%);
    background-size: 200% 100%;
  }

  .skeleton-page-btn {
    background: linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%);
    background-size: 200% 100%;
    border: 1px solid #30363d;
  }
}

@media (max-width: 1024px) {
  .skeleton-table-header, .skeleton-table-row { padding: 0.75rem 1rem; gap: 1rem; }
}
</style>