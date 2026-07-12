<template>
  <div class="base-list">
    <!-- Control Panel -->
    <div class="control-panel">
      <div class="panel-left">
        <button class="btn btn-primary" @click="$emit('create')" v-if="true">
          New
        </button>
        <button 
          v-if="selectedIds.length > 0" 
          class="btn btn-danger" 
          @click="$emit('bulk-delete', selectedIds)"
        >
          Delete ({{ selectedIds.length }})
        </button>
      </div>
      
      <div class="panel-right">
        <div class="record-pager" v-if="totalCount">
          <span class="pager-info">{{ pageRange }} / {{ totalCount }}</span>
          <div class="pager-btns">
            <button class="btn-pager" @click="prevPage" :disabled="offset === 0">
              ←
            </button>
            <button class="btn-pager" @click="nextPage" :disabled="isLastPage">
              →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Table Container -->
    <div class="table-view">
      <div v-if="loading" class="loading-state">
        <p>Loading...</p>
      </div>
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
      </div>
      
      <div class="table-responsive" v-else>
        <table class="table-clean">
          <thead>
            <tr>
              <th class="checkbox-cell">
                <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
              </th>
              <th v-for="key in visibleFields" :key="key">
                {{ getFieldLabel(key) }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id" @click="$emit('view', item.id)" class="item-row" :class="{ 'selected': selectedIds.includes(item.id) }">
              <td class="checkbox-cell" @click.stop>
                <input type="checkbox" :checked="selectedIds.includes(item.id)" @change="toggleSelect(item.id)" />
              </td>
              <td v-for="key in visibleFields" :key="key">
                {{ formatValue(item[key], key) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { formatDate } from '../../utils/dateUtils';

const props = defineProps<{
  title: string;
  items: any[];
  totalCount: number;
  offset: number;
  limit: number;
  metadata: any;
  loading: boolean;
  error?: string | null;
  search?: string;
  breadcrumbs: any[];
  groupedResults?: any[];
  activeGroupBy?: string;
  modelName?: string;
}>();

const emit = defineEmits(['view', 'create', 'refresh', 'search', 'paginate', 'breadcrumb-click', 'filter', 'group-by', 'bulk-delete']);

// State
const selectedIds = ref<number[]>([]);

// Selection Logic
const isAllSelected = computed(() => {
    return props.items.length > 0 && selectedIds.value.length === props.items.length;
});

const toggleSelectAll = (event: any) => {
    if (event.target.checked) {
        selectedIds.value = props.items.map(i => i.id);
    } else {
        selectedIds.value = [];
    }
};

const toggleSelect = (id: number) => {
    const idx = selectedIds.value.indexOf(id);
    if (idx === -1) {
        selectedIds.value.push(id);
    } else {
        selectedIds.value.splice(idx, 1);
    }
};

// Fields
const allFields = computed(() => props.metadata?.fields || {});

const visibleFields = computed(() => {
    const fields = Object.keys(allFields.value).filter(k => 
        k !== 'id' && k !== 'created_at' && k !== 'updated_at'
    ).slice(0, 6);
    return fields;
});

const getFieldLabel = (key: string) => {
    return allFields.value[key]?.label || key;
};

// Pagination
const pageRange = computed(() => {
    const start = props.offset + 1;
    const end = Math.min(props.offset + props.limit, props.totalCount);
    return `${start}-${end}`;
});

const isLastPage = computed(() => {
    return props.offset + props.limit >= props.totalCount;
});

const prevPage = () => {
    const newOffset = Math.max(0, props.offset - props.limit);
    emit('paginate', newOffset);
};

const nextPage = () => {
    if (!isLastPage.value) {
        emit('paginate', props.offset + props.limit);
    }
};

// Simple value formatting
const formatValue = (value: any, key: string) => {
    try {
        if (value === null || value === undefined) return '';
        
        const fieldType = allFields.value[key]?.type;
        
        if (fieldType === 'boolean') {
            return value ? 'Yes' : 'No';
        }
        
        if (fieldType === 'date' || fieldType === 'datetime') {
            if (typeof value === 'string' && value) {
                try {
                    return formatDate(value);
                } catch {
                    // Ignore date parsing errors
                }
            }
        }
        
        if (fieldType === 'many2one' && typeof value === 'object') {
            return value?.display_name || value?.name || value?.full_name || value?.id || '';
        }
        
        return String(value);
    } catch (error) {
        return String(value || '');
    }
};
</script>

<style lang="scss" scoped>
.base-list {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: v.$white;
  overflow: hidden;
}

.control-panel {
  flex: 0 0 auto;
  background: v.$white;
  border-bottom: 1px solid v.$table-border;
  padding: 10px;
  min-height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.panel-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.record-pager {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  .pager-info {
    font-size: 0.8125rem;
    color: v.$gray-500;
    font-weight: 500;
    white-space: nowrap;
  }
  
  .pager-btns {
    display: flex;
    gap: 1px;
    background: v.$table-border;
    border: 1px solid v.$table-border;
    border-radius: 4px;
    overflow: hidden;
  }
}

.btn-pager {
  background: v.$white;
  border: none;
  padding: 0.4rem 0.8rem;
  cursor: pointer;
  color: v.$gray-700;
  
  &:disabled {
    color: v.$disabled-text;
    cursor: not-allowed;
  }
  
  &:not(:disabled):hover {
    background: v.$table-hover;
  }
}

.table-view {
  flex: 1;
  overflow: auto;
  position: relative;
  display: flex;
  flex-direction: column;
}

.table-responsive {
  min-width: 100%;
  width: 100%;
  overflow-x: auto;
}

.table-clean {
  width: 100%;
  border-collapse: collapse;
  
  th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid v.$table-border;
  }
  
  th {
    background: v.$table-header-bg;
    font-weight: 600;
    color: v.$gray-500;
    font-size: 0.8125rem;
    text-transform: uppercase;
    letter-spacing: 0.025em;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .checkbox-cell {
    width: 44px;
    text-align: center;
    padding: 0;
    vertical-align: middle;
    
    input[type="checkbox"] {
      width: 18px;
      height: 18px;
      cursor: pointer;
      accent-color: v.$blue-500;
    }
  }
  
  .item-row {
    cursor: pointer;
    transition: background 0.15s;
    
    &:hover {
      background: v.$table-hover;
    }

    &.selected {
      background: v.$table-selected;
    }
  }
  
  td {
    font-size: 0.875rem;
    color: v.$gray-700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 300px;
  }
}

.btn {
  padding: 0 1.5rem;
  height: 36px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  border: 1px solid transparent;
  white-space: nowrap;
}

.btn-primary {
  background: v.$blue-500;
  color: v.$white;
  &:hover {
    background: v.$blue-600;
  }
}

.btn-danger {
  background: v.$red-500;
  color: v.$white;
  &:hover {
    background: v.$error-text;
  }
}

.loading-state, .error-state {
  padding: 4rem;
  text-align: center;
  color: v.$gray-500;
  margin: auto;
}
</style>