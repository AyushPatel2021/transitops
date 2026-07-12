<template>
  <div class="base-list">
    <!-- Mobile Header (Znova Style) -->
    <div v-if="isMobile" class="mobile-header-znova">
      <div class="mobile-header-content">
        <!-- Left: Back button and Title -->
        <div class="mobile-left-section">
          <button class="mobile-back-btn" @click="$emit('breadcrumb-click', breadcrumbs[breadcrumbs.length - 2], breadcrumbs.length - 2)" v-if="breadcrumbs.length > 1">
            <ArrowLeft class="icon-sm" />
          </button>
          <span class="page-title">{{ title || 'List' }}</span>
        </div>
        
        <!-- Right: Action buttons -->
        <div class="mobile-actions">
          <button class="mobile-action-btn" @click="showMobileSearch = !showMobileSearch">
            <Search class="icon-sm" />
          </button>
          <div class="mobile-pager-btns" v-if="totalCount">
            <button class="mobile-btn-pager" @click="prevPage" :disabled="offset === 0">
              <ChevronLeft class="icon-sm" />
            </button>
            <button class="mobile-btn-pager" @click="nextPage" :disabled="isLastPage">
              <ChevronRight class="icon-sm" />
            </button>
          </div>
        </div>
      </div>
      
      <!-- Mobile Search Bar (slides down when search icon clicked) -->
      <div v-if="showMobileSearch" class="mobile-search-bar">
        <AdvancedSearchBar
          :metadata="metadata"
          :search="search"
          :filters="activeFilters"
          :group-by="activeGroupBy"
          @search="handleSearch"
          @filter="handleFilter"
          @group-by="handleGroupBy"
          @clear="handleClearAll"
        />
      </div>
      
      <!-- Mobile New Button Row -->
      <div class="mobile-new-row">
        <button 
          v-if="selectedIds.length > 0 && actionPermissions.showDeleteButton" 
          class="btn btn-danger mobile-new-btn" 
          @click="$emit('bulk-delete', selectedIds)"
        >
          Delete ({{ selectedIds.length }})
        </button>
        <button 
          v-else-if="actionPermissions.showCreateButton"
          class="btn btn-primary mobile-new-btn" 
          @click="$emit('create')"
        >
          New
        </button>
        <div class="mobile-list-info" v-if="totalCount">
          <div class="mobile-pagination-info">
            <span class="page-info">{{ pageRange }} / {{ totalCount }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Desktop Action Bar (Reference Framework Style) -->
    <div v-else class="action-bar">
      <div class="action-bar-left">
        <button class="btn btn-primary" @click="$emit('create')" v-if="actionPermissions.showCreateButton">
          <span>New</span>
        </button>
        <button 
          v-if="selectedIds.length > 0 && actionPermissions.showDeleteButton" 
          class="btn btn-danger" 
          @click="$emit('bulk-delete', selectedIds)"
        >
          <Trash2 class="icon-sm" />
          <span>Delete ({{ selectedIds.length }})</span>
        </button>

        <!-- View Tabs (Hidden for now, as requested) -->
        <div class="view-tabs" style="display: none;">
          <button class="view-tab active">
            <LayoutList class="icon-xs" />
            <span>List</span>
          </button>
          <button class="view-tab">
            <LayoutGrid class="icon-xs" />
            <span>Kanban</span>
          </button>
        </div>
      </div>
      
      <div class="action-bar-center">
        <AdvancedSearchBar
          :metadata="metadata"
          :search="search"
          :filters="activeFilters"
          :group-by="localActiveGroupBy"
          @search="handleSearch"
          @filter="handleFilter"
          @group-by="handleGroupBy"
          @clear="handleClearAll"
        />
      </div>
 
      <div class="action-bar-right">
        <div class="pager-wrapper" v-if="totalCount">
          <div class="nav-arrows">
            <button class="nav-arrow" @click="prevPage" :disabled="offset === 0" title="Previous Page">
              <ChevronLeft class="icon-sm" />
            </button>
            <button class="nav-arrow" @click="nextPage" :disabled="isLastPage" title="Next Page">
              <ChevronRight class="icon-sm" />
            </button>
          </div>
          <span class="pager-info">{{ pageRange }} / {{ totalCount }}</span>
        </div>
      </div>
    </div>

    <!-- Table Container -->
    <div class="table-view">
      <TableSkeleton v-if="loading" part="table" :row-count="8" />
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
      </div>
      
      <div class="table-responsive" v-else :class="{ 'mobile-table': isMobile }">
        <div v-if="renderError" class="error-state">
          <p>Error rendering table: {{ renderError }}</p>
          <button @click="clearRenderError" class="btn btn-primary">Retry</button>
        </div>
        <table v-else class="table-clean">
          <thead>
            <tr>
              <th class="checkbox-cell">
                <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
              </th>
              <th v-for="key in visibleFields" :key="key" :style="getColumnStyle(allFields[key])">
                {{ allFields[key]?.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- Grouped View -->
            <template v-if="groupedResults && groupedResults.length > 0">
                <template v-for="group in groupedResults" :key="group.value">
                    <tr class="group-header" @click="toggleGroup(group.value)">
                        <td :colspan="visibleFields.length + 1" class="group-cell">
                            <div class="group-content">
                                <button class="group-toggle">
                                    <ChevronDown v-if="isGroupExpanded(group.value)" class="icon-sm" />
                                    <ChevronRight v-else class="icon-sm" />
                                </button>
                                <span class="group-title">{{ formatGroupHeader(group) }}</span>
                                <span class="group-count">({{ group.count }})</span>
                            </div>
                        </td>
                    </tr>
                    <template v-if="isGroupExpanded(group.value)">
                        <tr v-for="item in group.items" :key="item.id" @click="$emit('view', item.id)" class="item-row" :class="{ 'selected': selectedIds.includes(item.id) }">
                             <td class="checkbox-cell" @click.stop>
                                <input type="checkbox" :checked="selectedIds.includes(item.id)" @change="toggleSelect(item.id)" />
                             </td>
                             <td v-for="key in visibleFields" :key="key">
                                <template v-if="allFields[key]?.type === 'selection'">
                                  <span v-if="allFields[key]?.widget === 'normal'" :class="'text-' + (allFields[key]?.options?.[item[key]]?.color || 'default')">
                                    {{ (typeof allFields[key]?.options?.[item[key]] === 'object' ? allFields[key]?.options?.[item[key]]?.label : allFields[key]?.options?.[item[key]]) || '-' }}
                                  </span>
                                  <span v-else :class="['badge-pill', 'badge-' + (allFields[key]?.options?.[item[key]]?.color || 'default')]">
                                    {{ (typeof allFields[key]?.options?.[item[key]] === 'object' ? allFields[key]?.options?.[item[key]]?.label : allFields[key]?.options?.[item[key]]) || '-' }}
                                  </span>
                                </template>
                                <template v-else-if="allFields[key]?.type === 'many2one'">
                                   <span class="rel-link">{{ formatMany2One(item[key], allFields[key]) }}</span>
                                </template>
                                <template v-else>
                                  {{ safeFormatValue(item[key], allFields[key]?.type, allFields[key]) }}
                                </template>
                             </td>
                        </tr>
                    </template>
                </template>
            </template>
            
            <!-- Standard Flat View -->
            <template v-else>
                <tr v-for="item in safeItems" :key="item.id" @click="$emit('view', item.id)" :style="{ minHeight: touchTargetSize.minHeight }" class="item-row" :class="{ 'selected': selectedIds.includes(item.id) }">
                  <td class="checkbox-cell" @click.stop>
                    <input type="checkbox" :checked="selectedIds.includes(item.id)" @change="toggleSelect(item.id)" />
                  </td>
                  <td v-for="key in visibleFields" :key="key">
                    <template v-if="allFields[key]?.type === 'selection'">
                      <span v-if="allFields[key]?.widget === 'normal'" :class="'text-' + (allFields[key]?.options?.[item[key]]?.color || 'default')">
                        {{ (typeof allFields[key]?.options?.[item[key]] === 'object' ? allFields[key]?.options?.[item[key]]?.label : allFields[key]?.options?.[item[key]]) || '-' }}
                      </span>
                      <span v-else :class="['badge-pill', 'badge-' + (allFields[key]?.options?.[item[key]]?.color || 'default')]">
                        {{ (typeof allFields[key]?.options?.[item[key]] === 'object' ? allFields[key]?.options?.[item[key]]?.label : allFields[key]?.options?.[item[key]]) || '-' }}
                      </span>
                    </template>
                    <template v-else-if="allFields[key]?.type === 'many2one'">
                       <span class="rel-link">{{ formatMany2One(item[key], allFields[key]) }}</span>
                    </template>
                    <template v-else>
                      {{ safeFormatValue(item[key], allFields[key]?.type, allFields[key]) }}
                    </template>
                  </td>
                </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pagination Footer (Standalone Block) -->
    <div class="pagination-footer" v-if="totalCount || (loading && !isMobile)">
      <TableSkeleton v-if="loading" part="pager" />
      <div v-else-if="totalCount" class="pagination">
        <div class="pagination-info">
          Showing <span class="bold">{{ offset + 1 }}-{{ Math.min(offset + limit, totalCount) }}</span> of <span class="bold">{{ totalCount }}</span> records
        </div>
        <div class="pagination-controls">
          <button class="pagination-btn" @click="prevPage" :disabled="offset === 0">
            <ChevronLeft class="icon-xs" />
          </button>
          <template v-for="page in visiblePages" :key="page">
            <button 
              class="pagination-btn" 
              :class="{ active: currentPage === page }"
              @click="gotoPage(page)"
            >
              {{ page }}
            </button>
          </template>
          <button class="pagination-btn" @click="nextPage" :disabled="isLastPage">
            <ChevronRight class="icon-xs" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, onErrorCaptured } from 'vue';
import { 
  ChevronLeft, 
  ChevronRight,
  ChevronDown,
  Search,
  ArrowLeft,
  Settings,
  MoreVertical,
  Plus,
  Trash2,
  LayoutList,
  LayoutGrid
} from 'lucide-vue-next';
import Breadcrumbs from '../common/Breadcrumbs.vue';
import NotificationBell from '../common/NotificationBell.vue';
import AdvancedSearchBar from './AdvancedSearchBar.vue';
import TableSkeleton from '../skeleton/TableSkeleton.vue';
import { useResponsive } from '../../composables/useResponsive';
import { formatDateTime, formatDate } from '../../utils/dateUtils';
import { useUnifiedPermissions } from '../../composables/useUnifiedPermissions';

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
  filters?: any[];
  groupBy?: string;
  breadcrumbs: any[];
  groupedResults?: any[];
  activeGroupBy?: string;
  modelName?: string; // Add modelName prop for permissions
}>();

const emit = defineEmits(['view', 'create', 'refresh', 'search', 'paginate', 'breadcrumb-click', 'filter', 'group-by', 'bulk-delete']);

// Initialize responsive composable
const { isMobile, isTablet, isDesktop, isTouchDevice, getEssentialColumns, touchTargetSize } = useResponsive();

// Initialize unified permissions composable (for list view, no specific record)
const { actionPermissions } = useUnifiedPermissions(props.modelName || '', 'list');

interface SearchField {
    key: string;
    label: string;
}

// State
const showMobileSearch = ref(false);
const activeFilters = ref<any[]>([]);
const localActiveGroupBy = ref<string>('');
const expandedGroups = ref<Set<string>>(new Set());
const selectedIds = ref<number[]>([]);
const renderError = ref<string | null>(null);

// Watch props to sync local state
watch([() => props.filters, () => props.metadata], ([newFilters, newMetadata]) => {
  
  // Check if metadata is actually loaded (has search_config with filters, or has fields)
  const hasSearchConfig = newMetadata?.search_config && Object.keys(newMetadata.search_config).length > 0;
  const hasFields = newMetadata?.fields && Object.keys(newMetadata.fields).length > 0;
  const isMetadataLoaded = hasSearchConfig || hasFields;
  
  if (newFilters && newFilters.length > 0) {
    if (isMetadataLoaded && newMetadata.search_config?.filters) {
      // We have both filters and metadata - convert filter names to objects
      const availableFilters = newMetadata.search_config.filters;
      const mappedFilters = newFilters.map(filterName => {
        const found = availableFilters.find((f: any) => f.name === filterName);
        return found;
      }).filter(Boolean);
      
      activeFilters.value = mappedFilters;
    } else {
      // Metadata not loaded yet - keep current activeFilters and don't clear them
    }
  } else if (newFilters && newFilters.length === 0) {
    // Explicitly empty filters array - clear activeFilters
    activeFilters.value = [];
  } else if (!newFilters && isMetadataLoaded) {
    // No filters prop and metadata is loaded - clear activeFilters
    activeFilters.value = [];
  }
  // If newFilters is undefined/null and metadata not loaded, do nothing (keep current state)
}, { immediate: true });

watch(() => props.groupBy, (newGroupBy) => {
  if (newGroupBy !== undefined) {
    localActiveGroupBy.value = newGroupBy;
  }
}, { immediate: true });

const safeItems = computed(() => {
  try {
    return props.items || [];
  } catch (error) {
    return [];
  }
});

// Selection Logic
const isAllSelected = computed(() => {
    return safeItems.value.length > 0 && selectedIds.value.length === safeItems.value.length;
});

const toggleSelectAll = (event: any) => {
    if (event.target.checked) {
        selectedIds.value = safeItems.value.map(i => i.id);
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

// Reset selection on pagination or search
watch(() => [safeItems.value, props.offset], () => {
    selectedIds.value = [];
});

// Auto-expand all groups when grouped results change
watch(() => props.groupedResults, (newVal) => {
    if (newVal && newVal.length > 0) {
        // Expand all by default
        const allKeys = newVal.map((g: any) => g.value); // Backend now returns 'value' for the group key
        expandedGroups.value = new Set(allKeys);
    } else {
        expandedGroups.value = new Set();
    }
}, { immediate: true });

const toggleGroup = (groupValue: string) => {
    const newSet = new Set(expandedGroups.value);
    if (newSet.has(groupValue)) {
        newSet.delete(groupValue);
    } else {
        newSet.add(groupValue);
    }
    expandedGroups.value = newSet;
};

const isGroupExpanded = (groupValue: string) => expandedGroups.value.has(groupValue);

const allFields = computed(() => props.metadata.fields || {});
const viewDef = computed(() => props.metadata.views?.list || {});

const visibleFields = computed(() => {
    if (viewDef.value.fields?.length) {
        const allColumns = viewDef.value.fields;
        return getEssentialColumns(allColumns, props.metadata);
    }
    const allColumns = Object.keys(allFields.value).filter(k => 
        k !== 'id' && k !== 'created_at' && k !== 'updated_at' && 
        allFields.value[k].type !== 'text'
    ).slice(0, 6);
    return getEssentialColumns(allColumns, props.metadata);
});

watch(() => props.activeGroupBy, (newVal) => {
    if (newVal !== undefined) {
        localActiveGroupBy.value = newVal;
    }
}, { immediate: true });

const pageRange = computed(() => {
    const start = props.offset + 1;
    const end = Math.min(props.offset + props.limit, props.totalCount);
    return `${start}-${end}`;
});

const isLastPage = computed(() => {
    return props.offset + props.limit >= props.totalCount;
});

const totalPages = computed(() => {
    return Math.ceil(props.totalCount / props.limit);
});

const currentPage = computed(() => {
    return Math.floor(props.offset / props.limit) + 1;
});

const visiblePages = computed(() => {
    const total = totalPages.value;
    const current = currentPage.value;
    const pages = [];
    
    // Show up to 5 pages around current
    let start = Math.max(1, current - 2);
    let end = Math.min(total, start + 4);
    
    if (end === total) {
        start = Math.max(1, end - 4);
    }
    
    for (let i = start; i <= end; i++) {
        pages.push(i);
    }
    return pages;
});

const gotoPage = (page: number) => {
    const newOffset = (page - 1) * props.limit;
    emit('paginate', newOffset);
};

const prevPage = () => {
    const newOffset = Math.max(0, props.offset - props.limit);
    emit('paginate', newOffset);
};

const nextPage = () => {
    if (!isLastPage.value) {
        emit('paginate', props.offset + props.limit);
    }
};

const handleSearch = (searchData: { query: string, field: string }) => {
    emit('search', searchData);
};

const handleFilter = (filters: any[]) => {
    // Store names for AdvancedSearchBar prop
    activeFilters.value = filters.map(f => f.name);
    // Emit full objects to parent (GenericView handles normalization)
    emit('filter', filters);
};

const handleGroupBy = (groupBy: string) => {
    localActiveGroupBy.value = groupBy;
    emit('group-by', groupBy);
};

const handleClearAll = () => {
    activeFilters.value = [];
    localActiveGroupBy.value = '';
    emit('search', { query: '', field: '' });
    emit('filter', []);
    emit('group-by', '');
};

// Safe wrapper that never throws errors
const safeFormatValue = (value: any, type: string, field: any) => {
  try {
    // Early return for null/undefined values
    if (value === null || value === undefined) return '';
    
    // Handle boolean type
    if (type === 'boolean') return value ? 'Yes' : 'No';
    
    // Handle date/datetime types
    if (type === 'date' || type === 'datetime') {
      // Simple date formatting
      if (value && typeof value === 'string') {
        try {
          if (type === 'date') {
            return formatDate(value);
          } else {
            return formatDateTime(value);
          }
        } catch {
          // Ignore date parsing errors
        }
      }
      return value || '';
    }
    
    // Return the value as-is for other types
    return value;
  } catch (error) {
    // Ultimate fallback - never throw
    return value ? String(value) : '';
  }
};

const clearRenderError = () => {
  renderError.value = null;
};

// Capture any errors in child components or template rendering
onErrorCaptured((error, instance, info) => {
  renderError.value = `Template error: ${error.message}`;
  return false; // Prevent the error from propagating further
});

const formatGroupHeader = (group: any) => {
    const rawValue = group.group_value;
    if (rawValue === null || rawValue === undefined) return group.value || 'Undefined';
    
    const groupBy = localActiveGroupBy.value;
    if (!groupBy) return group.value || rawValue;
    
    // Look up field info
    const searchConfig = props.metadata?.search_config || {};
    const groupByConfig = (searchConfig.group_by || []).find((g: any) => g.name === groupBy);
    
    const fieldName = groupByConfig ? groupByConfig.field : groupBy;
    const field = allFields.value[fieldName];
    
    if (field && (field.type === 'date' || field.type === 'datetime')) {
        return safeFormatValue(rawValue, field.type, field);
    }
    
    return group.value || rawValue;
};

const formatMany2One = (val: any, field: any) => {
  try {
    if (!val) return '';
    if (typeof val === 'object') {
      const recName = field?.rec_name || 'display_name';
      return val[recName] || val.display_name || val.name || val.full_name || val.id || '';
    }
    return `#${val}`;
  } catch (error) {
    return val ? String(val) : '';
  }
};

const getColumnStyle = (field: any) => {
    if (!field) return {};
    if (field.type === 'date') return { width: '150px' };
    if (field.type === 'selection') return { width: '120px' };
    return {};
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;
@use "sass:color";

.base-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: v.$bg-main;
  min-height: 0;
  position: relative;
  overflow: visible; /* Changed to allow dropdowns to extend beyond */
  width: 100%; /* Ensure full width */
}

/* --- Znova-Style Mobile Header --- */
.mobile-header-znova {
  flex: 0 0 auto;
  background: v.$white;
  border-bottom: 1px solid v.$border-color;
  z-index: 30;
}

.mobile-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  height: 56px;
}

.mobile-left-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
  
  .page-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: v.$text-primary;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.mobile-back-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: v.$text-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  min-width: 44px;
  min-height: 44px;
  flex-shrink: 0;
  
  &:hover {
    background: v.$bg-main;
  }
}

.mobile-title-center {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  
  .page-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: v.$text-primary;
    white-space: nowrap;
  }
}

.mobile-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mobile-action-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: v.$text-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  min-width: 44px;
  min-height: 44px;
  
  &:hover {
    background: v.$bg-main;
  }
  
  &:disabled {
    color: v.$text-disabled;
    cursor: not-allowed;
  }
}

.mobile-pager-btns {
  display: flex;
  gap: 1px;
  background: v.$border-color;
  border: 1px solid v.$border-color;
  border-radius: 4px;
  overflow: hidden;
}

.mobile-btn-pager {
  background: v.$white;
  border: none;
  padding: 0.4rem;
  display: flex;
  align-items: center;
  cursor: pointer;
  color: v.$text-primary;
  
  &:disabled {
    color: v.$text-disabled;
    cursor: not-allowed;
  }
  
  &:not(:disabled):hover {
    background: v.$bg-main;
  }
}

.mobile-search-bar {
  background: v.$bg-main;
  border-bottom: 1px solid v.$border-color;
  padding: 0.75rem 1rem;
  animation: slideDown 0.2s ease-out;
  position: relative; /* Add this for dropdown positioning */
}

.search-input-container {
  display: flex;
  align-items: center;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 6px;
  padding: 0 0.75rem;
  position: relative; /* Add this for dropdown positioning */
  
  .search-icon {
    width: 16px;
    height: 16px;
    color: v.$text-secondary;
    margin-right: 0.5rem;
  }
  
  .mobile-search-input {
    flex: 1;
    border: none;
    outline: none;
    padding: 0.75rem 0;
    font-size: 1rem;
    color: v.$text-primary;
    
    &::placeholder {
      color: v.$text-placeholder;
    }
  }
  
  .search-close-btn {
    background: none;
    border: none;
    padding: 0.25rem;
    cursor: pointer;
    color: v.$text-secondary;
    font-size: 1.25rem;
    line-height: 1;
    
    &:hover {
      color: v.$text-primary;
    }
  }
}

.mobile-search-dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 1rem;
  right: 1rem;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 6px;
  box-shadow: 0 4px 6px -1px v.$shadow-light;
  z-index: 1000; /* Increase z-index to ensure it's above other elements */
  max-height: 200px;
  overflow-y: auto;
  
  .search-option {
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: v.$text-primary;
    transition: background 0.15s;

    &:hover, &.active {
      background: v.$border-light;
    }

    .icon-xs {
      width: 12px;
      height: 12px;
      color: v.$primary-color;
    }

    strong {
      font-weight: 600;
      color: v.$primary-color;
    }
  }
}

.mobile-new-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: v.$bg-main;
  border-bottom: 1px solid v.$border-color;
}

.mobile-new-btn {
  flex: 1;
  max-width: 120px;
}

.base-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: v.$bg-main;
  width: 100%; /* Ensure full width */
}

.mobile-list-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.mobile-pagination-info {
  .page-info {
    font-size: 0.875rem;
    color: v.$text-secondary;
    font-weight: 500;
    white-space: nowrap;
  }
}

@keyframes slideDown {
  from { 
    opacity: 0;
    transform: translateY(-10px); 
  }
  to { 
    opacity: 1;
    transform: translateY(0); 
  }
}

/* --- Desktop Action Bar --- */
.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  margin: 24px;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 16px; // radius-lg
  flex-shrink: 0;
  gap: 24px;
  box-shadow: v.$shadow-sm;
  z-index: 20;
}

// Dark mode action bar
[data-theme="dark"] .action-bar {
  background: #161b22;
  border-color: #30363d;
}

.action-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-bar-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 600px;
}

.action-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* View Tabs (Placeholder style) */
.view-tabs {
  display: flex;
  gap: 2px;
  background: v.$bg-main;
  padding: 4px;
  border-radius: 10px;
  border: 1px solid v.$border-color;

  .view-tab {
    padding: 6px 12px;
    background: transparent;
    border: none;
    color: v.$text-secondary;
    cursor: pointer;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;

    &:hover {
      color: v.$text-primary;
      background: v.$white;
    }

    &.active {
      background: v.$white;
      color: v.$primary-color;
      box-shadow: v.$shadow-sm;
    }
  }
}

// Dark mode view tabs
[data-theme="dark"] .view-tabs {
  background: #0d1117;
  border-color: #30363d;
  
  .view-tab {
    color: #7d8590;
    
    &:hover {
      color: #e6edf3;
      background: #161b22;
    }
    
    &.active {
      background: #161b22;
      color: #2563eb;
    }
  }
}

/* Pager & Arrows */
.pager-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-arrows {
  display: flex;
  gap: 2px;
  background: v.$bg-main;
  padding: 4px;
  border-radius: v.$radius-btn;
  border: 1px solid v.$border-color;
}

// Dark mode nav arrows
[data-theme="dark"] .nav-arrows {
  background: #0d1117;
  border-color: #30363d;
}

.nav-arrow {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: v.$text-secondary;
  cursor: pointer;
  border-radius: v.$radius-btn;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: v.$white;
    color: v.$text-primary;
    box-shadow: v.$shadow-sm;
  }

  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
}

// Dark mode nav arrow
[data-theme="dark"] .nav-arrow {
  color: #7d8590;
  
  &:hover:not(:disabled) {
    background: #161b22;
    color: #e6edf3;
  }
}

.pager-info {
  font-size: 14px;
  color: v.$text-secondary;
  font-weight: 500;
  padding: 0 4px;
  min-width: 70px;
  text-align: center;
}

// Dark mode pager info
[data-theme="dark"] .pager-info {
  color: #7d8590;
}

/* --- Search Bar --- */
.search-bar-container {
    position: relative;
    width: 100%;
}

.search-bar {
  display: flex;
  align-items: center;
  background: v.$border-light;
  border-radius: 6px;
  padding: 0 0.75rem;
  height: 36px;
  border: 1px solid v.$border-color;
  transition: all 0.2s;
  
  &:focus-within {
    background: v.$white;
    border-color: v.$primary-color;
    box-shadow: 0 0 0 2px rgba(v.$primary-color, 0.1);
  }
  
  .search-icon {
    width: 14px;
    height: 14px;
    color: v.$text-secondary;
    margin-right: 0.5rem;
    flex-shrink: 0;
  }
  
  input {
    border: none;
    background: transparent;
    outline: none;
    width: 100%;
    font-size: 0.875rem;
    color: v.$text-primary;
    
    &::placeholder {
      color: v.$text-placeholder;
    }
  }
}

.search-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    margin-top: 4px;
    background: v.$white;
    border: 1px solid v.$border-color;
    border-radius: 6px;
    box-shadow: 0 10px 15px -3px v.$shadow-color-md;
    z-index: 100;
    overflow: hidden;

    .search-option {
        padding: 0.6rem 1rem;
        font-size: 0.875rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: v.$text-primary;
        transition: background 0.15s;

        &:hover, &.active {
            background: v.$border-light;
        }

        .icon-xs {
            width: 12px;
            height: 12px;
            color: v.$primary-color;
        }

        strong {
            font-weight: 600;
            color: v.$primary-color;
        }
    }
}

/* --- Table View & Clean Table Refinements --- */
/* --- Table View & Clean Table Refinements --- */
.table-view {
  flex: 0 1 auto;
  max-height: calc(100vh - 280px);
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 16px; // radius-lg
  margin: 0 24px 12px 24px; // Bottom margin to separate from pager
  overflow: visible; // Changed from hidden to allow dropdowns to extend
  display: flex;
  flex-direction: column;
  box-shadow: v.$shadow-sm;

  .table-responsive {
    flex: 1;
    overflow: auto;
    -webkit-overflow-scrolling: touch;
    border-radius: 16px; // Match parent radius

    .table-clean {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;

      th {
        padding: 12px 16px;
        background: v.$bg-main;
        border-bottom: 1px solid v.$border-color;
        font-size: 13px;
        font-weight: 600;
        color: v.$text-secondary;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        position: sticky;
        top: 0;
        z-index: 10;
        text-align: left;
        vertical-align: middle;
      }

      td {
        padding: 12px 16px;
        border-bottom: 1px solid v.$border-color;
        font-size: 14px;
        color: v.$text-primary;
        vertical-align: middle;
      }

      .item-row {
        transition: background 0.2s;
        cursor: pointer;

        &:hover {
          background: v.$bg-main;
        }

        &.selected {
          background: rgba(v.$primary-color, 0.05);
        }
      }

      .checkbox-cell {
        width: 40px;
        padding: 0;
        text-align: center;
        vertical-align: middle;
        
        input[type="checkbox"] {
          width: 18px;
          height: 18px;
          accent-color: v.$primary-color;
          cursor: pointer;
          display: block;
          margin: auto;
        }
      }

      /* Group Header Styles */
      .group-header {
        background-color: v.$bg-main;
        cursor: pointer;
        font-weight: 600;
        
        &:hover {
          background-color: rgba(v.$primary-color, 0.03);
        }

        .group-content {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0 12px;
        }
        
        .group-toggle {
          background: none;
          border: none;
          display: flex;
          align-items: center;
          color: v.$text-secondary;
          cursor: pointer;
          padding: 0;
        }
        
        .group-title {
          font-size: 13px;
          color: v.$text-primary;
          line-height: 1;
          display: flex;
          align-items: center;
        }
        
        .group-count {
          color: v.$text-secondary;
          font-weight: 400;
          font-size: 13px;
          line-height: 1;
          display: flex;
          align-items: center;
          margin-left: 0.25rem;
        }
      }
    }
  }
}

// Dark mode table view
[data-theme="dark"] .table-view {
  background: #161b22;
  border-color: #30363d;
  
  .table-responsive .table-clean {
    th {
      background: #1c2128;
      border-bottom-color: #30363d;
      color: #7d8590;
    }
    
    td {
      border-bottom-color: #30363d;
      color: #e6edf3;
    }
    
    .item-row {
      &:hover {
        background: #1c2128;
      }
      
      &.selected {
        background: rgba(37, 99, 235, 0.1);
      }
    }
    
    .checkbox-cell input[type="checkbox"] {
      accent-color: #2563eb;
    }
    
    .group-header {
      background-color: #1c2128;
      
      &:hover {
        background-color: rgba(37, 99, 235, 0.05);
      }
      
      .group-toggle {
        color: #7d8590;
      }
      
      .group-title {
        color: #e6edf3;
      }
      
      .group-count {
        color: #7d8590;
      }
    }
  }
}

/* --- Pagination Footer (Standalone Block) --- */
.pagination-footer {
  margin: 0 24px 24px 24px;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 16px; // radius-lg
  padding: 12px 20px;
  box-shadow: v.$shadow-sm;
  flex-shrink: 0;

  .pagination {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .pagination-info {
      font-size: 14px;
      color: v.$text-secondary;
      
      .bold {
        font-weight: 600;
        color: v.$text-primary;
      }
    }

    .pagination-controls {
      display: flex;
      gap: 4px;

      .pagination-btn {
        height: 32px;
        min-width: 32px;
        padding: 0 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: v.$white;
        border: 1px solid v.$border-color;
        border-radius: v.$radius-btn;
        font-size: 14px;
        font-weight: 500;
        color: v.$text-secondary;
        cursor: pointer;
        transition: all 0.2s;

        &:hover:not(:disabled) {
          border-color: v.$primary-color;
          color: v.$primary-color;
          background: v.$white;
          box-shadow: v.$shadow-sm;
        }

        &.active {
          background: rgba(v.$primary-color, 0.1);
          border-color: v.$primary-color;
          color: v.$primary-color;
          font-weight: 600;
        }

        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          background: v.$bg-main;
        }

        .icon-xs {
          width: 16px;
          height: 16px;
        }
      }
    }
  }
}

// Dark mode pagination footer
[data-theme="dark"] .pagination-footer {
  background: #161b22;
  border-color: #30363d;
  
  .pagination {
    .pagination-info {
      color: #7d8590;
      
      .bold {
        color: #e6edf3;
      }
    }
    
    .pagination-controls {
      .pagination-btn {
        background: #1c2128;
        border-color: #30363d;
        color: #e6edf3;
        
        &:hover:not(:disabled) {
          background: #0d1117;
          border-color: #2563eb;
          color: #2563eb;
        }
        
        &.active {
          background: #2563eb;
          border-color: #2563eb;
          color: white;
        }
        
        &:disabled {
          opacity: 0.4;
          background: #1c2128;
        }
      }
    }
  }
}

/* --- UI Elements --- */
.btn {
  padding: 0 1.5rem;
  height: 36px;
  border-radius: v.$radius-btn; // Specific 10px for buttons
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

.btn-sm {
  padding: 0 1rem;
  height: 32px;
  font-size: 0.8125rem;
}

.btn-primary {
  background: v.$primary-color;
  color: v.$white;
  &:hover {
    background: v.$primary-hover;
  }
}

.badge-pill {
  padding: 0.125rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  display: inline-block;
  
  &.badge-success { background: rgba(v.$success-color, 0.1); color: v.$success-color; }
  &.badge-danger { background: rgba(v.$danger-color, 0.1); color: v.$danger-color; }
  &.badge-warning { background: rgba(v.$warning-color, 0.1); color: v.$warning-color; }
  &.badge-primary { background: rgba(v.$primary-color, 0.1); color: v.$primary-color; }
  &.badge-info { background: rgba(v.$info-color, 0.1); color: v.$info-color; }
  &.badge-secondary { background: v.$text-disabled; color: v.$text-secondary; }
  &.badge-default { background: v.$border-light; color: v.$text-tertiary; }
}

// Dark mode badges
[data-theme="dark"] .badge-pill {
  &.badge-success { 
    background: rgba(16, 185, 129, 0.15); 
    color: #3fb950; 
  }
  &.badge-danger { 
    background: rgba(239, 68, 68, 0.15); 
    color: #f85149; 
  }
  &.badge-warning { 
    background: rgba(245, 158, 11, 0.15); 
    color: #d29922; 
  }
  &.badge-primary { 
    background: rgba(37, 99, 235, 0.15); 
    color: #58a6ff; 
  }
  &.badge-info { 
    background: rgba(59, 130, 246, 0.15); 
    color: #58a6ff; 
  }
  &.badge-secondary { 
    background: #30363d; 
    color: #7d8590; 
  }
  &.badge-default { 
    background: #30363d; 
    color: #7d8590; 
  }
}

.text-success { color: v.$success-color; font-weight: 500; }
.text-danger { color: v.$danger-color; font-weight: 500; }
.text-warning { color: v.$warning-color; font-weight: 500; }
.text-primary { color: v.$primary-color; font-weight: 500; }
.text-info { color: v.$info-color; font-weight: 500; }
.text-secondary { color: v.$text-secondary; font-weight: 500; }
.text-default { color: v.$text-primary; }

// Dark mode text colors
[data-theme="dark"] {
  .text-success { color: #3fb950; }
  .text-danger { color: #f85149; }
  .text-warning { color: #d29922; }
  .text-primary { color: #58a6ff; }
  .text-info { color: #58a6ff; }
  .text-secondary { color: #7d8590; }
  .text-default { color: #e6edf3; }
}

.rel-link {
  color: v.$primary-color;
  font-weight: 500;
  &:hover {
    text-decoration: underline;
  }
}

.icon-sm { width: 16px; height: 16px; }

.error-state {
  padding: 4rem;
  text-align: center;
  color: v.$text-secondary;
  margin: auto;
}
</style>
