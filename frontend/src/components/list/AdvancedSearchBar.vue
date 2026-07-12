<template>
  <div class="znova-search-container">
    <!-- Main Search Bar -->
    <div class="search-bar-main">
      <!-- Search Input Wrapper with Pills Inside -->
      <div class="search-input-wrapper">
        <Search class="search-icon" />
        
        <!-- Middle content area that wraps -->
        <div class="search-content-wrapper">
          <!-- Active Filter Pills Inside Search Bar -->
          <div class="inline-pills-container" v-if="activeFilters.length > 0 || activeGroupBy">
            <!-- Filter Pills -->
            <div 
              v-for="filter in activeFilters" 
              :key="filter.name"
              class="filter-pill"
              :class="'filter-' + filter.name"
            >
              <span class="pill-icon">🔍</span>
              <span class="pill-text">{{ filter.label }}</span>
              <button @click="removeFilter(filter.name)" class="pill-remove">
                <X class="icon-xs" />
              </button>
            </div>
            
            <!-- Group By Pill -->
            <div v-if="activeGroupBy" class="filter-pill group-by-pill">
              <span class="pill-icon">📊</span>
              <span class="pill-text">{{ getGroupByLabel(activeGroupBy) }}</span>
              <button @click="removeGroupBy" class="pill-remove">
                <X class="icon-xs" />
              </button>
            </div>
          </div>
          
          <input 
            ref="searchInput"
            type="text" 
            placeholder="Search..."
            v-model="searchQuery"
            @input="onSearchInput"
            @focus="onSearchFocus"
            @keydown="onKeyDown"
            class="search-input"
          />
        </div>
        
        <!-- Right side actions - stay fixed -->
        <div class="search-actions">
          <!-- Clear Button -->
          <button 
            v-if="searchQuery || activeFilters.length > 0 || activeGroupBy"
            @click="clearAll" 
            class="search-clear"
          >
            <X class="icon-sm" />
          </button>
          
          <!-- Filter Toggle Button -->
          <button 
            @click="toggleFilterDropdown" 
            class="filter-toggle"
            :class="{ active: showFilterDropdown }"
          >
            <Filter class="icon-sm" />
          </button>
        </div>
      </div>
      
      <!-- Search Suggestions Dropdown -->
      <div v-if="showSearchDropdown && searchQuery && searchableFields.length > 0" class="search-suggestions">
        <div 
          v-for="(field, index) in searchableFields" 
          :key="field.key" 
          :class="['suggestion-item', { active: index === activeSearchIndex }]"
          @click="executeSearch(field.key)"
          @mouseenter="activeSearchIndex = index"
        >
          <Search class="icon-xs" />
          <span>Search <strong>{{ field.label }}</strong> for: <strong>{{ searchQuery }}</strong></span>
        </div>
      </div>
    </div>
    
    <!-- Filter Dropdown Panel -->
    <div v-if="showFilterDropdown" class="filter-panel">
      <div class="filter-panel-content">
        <!-- Filters Section -->
        <div class="filter-section">
          <div class="section-header">
            <Filter class="icon-sm" />
            <span class="section-title">Filters</span>
          </div>
          <div class="filter-options">
            <div 
              v-for="filter in availableFilters" 
              :key="filter.name"
              class="filter-option"
              :class="{ active: isFilterActive(filter.name) }"
              @click="toggleFilter(filter)"
            >
              <div class="filter-checkbox">
                <div v-if="isFilterActive(filter.name)" class="checkbox-checked">✓</div>
              </div>
              <span class="filter-label">{{ filter.label }}</span>
            </div>
          </div>
        </div>
        
        <!-- Group By Section -->
        <div class="filter-section">
          <div class="section-header">
            <BarChart3 class="icon-sm" />
            <span class="section-title">Group By</span>
          </div>
          <div class="filter-options">
            <div 
              v-for="group in availableGroupBy" 
              :key="group.name"
              class="filter-option"
              :class="{ active: activeGroupBy === group.name }"
              @click="toggleGroupBy(group)"
            >
              <div class="filter-checkbox">
                <div v-if="activeGroupBy === group.name" class="checkbox-checked">✓</div>
              </div>
              <span class="filter-label">{{ group.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { Search, Filter, X, BarChart3 } from 'lucide-vue-next';

interface SearchField {
  key: string;
  label: string;
  type: string;
}

interface FilterOption {
  name: string;
  label: string;
  domain: string;
  default: boolean;
}

interface GroupByOption {
  name: string;
  label: string;
  field: string;
  date_group?: string;
}

const props = defineProps<{
  metadata: any;
  search?: string;
  filters?: Array<string | FilterOption>;
  groupBy?: string;
}>();

const emit = defineEmits(['search', 'filter', 'group-by', 'clear']);

// Refs
const searchInput = ref<HTMLInputElement>();
const searchQuery = ref('');
const showSearchDropdown = ref(false);
const showFilterDropdown = ref(false);
const activeSearchIndex = ref(0);

// State
const activeFilters = ref<FilterOption[]>([]);
const activeGroupBy = ref<string>('');

// Computed
const searchableFields = computed<SearchField[]>(() => {
  const listView = props.metadata?.views?.list;
  if (listView?.search_fields) {
    return listView.search_fields.map((key: string) => ({
      key,
      label: props.metadata.fields[key]?.label || key,
      type: props.metadata.fields[key]?.type || 'string'
    }));
  }
  
  // Fallback to first few fields
  const fields = Object.keys(props.metadata?.fields || {});
  return fields.slice(0, 5).map(key => ({
    key,
    label: props.metadata.fields[key]?.label || key,
    type: props.metadata.fields[key]?.type || 'string'
  }));
});

const availableFilters = computed<FilterOption[]>(() => {
  return props.metadata?.search_config?.filters || [];
});

const availableGroupBy = computed<GroupByOption[]>(() => {
  return props.metadata?.search_config?.group_by || [];
});

// Methods
const getGroupByLabel = (groupByName: string): string => {
  const group = availableGroupBy.value.find(g => g.name === groupByName);
  return group ? group.label : groupByName;
};

const isFilterActive = (filterName: string): boolean => {
  return activeFilters.value.some(f => f.name === filterName);
};

const toggleFilter = (filter: FilterOption) => {
  const index = activeFilters.value.findIndex(f => f.name === filter.name);
  if (index >= 0) {
    activeFilters.value.splice(index, 1);
  } else {
    activeFilters.value.push(filter);
  }
  emitFilters();
};

const removeFilter = (filterName: string) => {
  activeFilters.value = activeFilters.value.filter(f => f.name !== filterName);
  emitFilters();
};

const toggleGroupBy = (group: GroupByOption) => {
  if (activeGroupBy.value === group.name) {
    activeGroupBy.value = '';
  } else {
    activeGroupBy.value = group.name;
  }
  emit('group-by', activeGroupBy.value);
};

const removeGroupBy = () => {
  activeGroupBy.value = '';
  emit('group-by', '');
};

const clearAll = () => {
  searchQuery.value = '';
  activeFilters.value = [];
  activeGroupBy.value = '';
  showSearchDropdown.value = false;
  showFilterDropdown.value = false;
  
  emit('clear');
};

const emitFilters = () => {
  emit('filter', activeFilters.value);
};

const onSearchInput = () => {
  // Close filter dropdown when typing
  showFilterDropdown.value = false;
  
  if (searchQuery.value.trim()) {
    showSearchDropdown.value = true;
    activeSearchIndex.value = 0;
  } else {
    showSearchDropdown.value = false;
    // Only emit search clear if search was previously active
    // Don't clear filters/groupBy here
    if (!searchQuery.value) {
      emit('search', { query: '', field: '' });
    }
  }
};

const onSearchFocus = () => {
  if (searchQuery.value.trim() && searchableFields.value.length > 0) {
    showSearchDropdown.value = true;
  }
};

const onKeyDown = (e: KeyboardEvent) => {
  if (showSearchDropdown.value && searchableFields.value.length > 0) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeSearchIndex.value = (activeSearchIndex.value + 1) % searchableFields.value.length;
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeSearchIndex.value = (activeSearchIndex.value - 1 + searchableFields.value.length) % searchableFields.value.length;
    } else if (e.key === 'Enter') {
      e.preventDefault();
      executeSearch(searchableFields.value[activeSearchIndex.value].key);
    } else if (e.key === 'Escape') {
      showSearchDropdown.value = false;
    }
  }
};

const executeSearch = (fieldKey: string) => {
  emit('search', { query: searchQuery.value, field: fieldKey });
  showSearchDropdown.value = false;
};

const toggleFilterDropdown = () => {
  showFilterDropdown.value = !showFilterDropdown.value;
  showSearchDropdown.value = false;
};

// Outside click handler
const handleOutsideClick = (e: Event) => {
  const target = e.target as HTMLElement;
  if (!target.closest('.znova-search-container')) {
    showSearchDropdown.value = false;
    showFilterDropdown.value = false;
  }
};

// Watch for prop changes
watch(() => props.search, (newVal) => {
  if (newVal !== undefined) {
    searchQuery.value = newVal || '';
  }
}, { immediate: true });

watch(() => props.filters, (newVal) => {
  
  if (newVal && Array.isArray(newVal)) {
    // Check if newVal contains filter objects or filter names
    if (newVal.length > 0 && typeof newVal[0] === 'object' && 'name' in newVal[0]) {
      // Already filter objects - use directly
      activeFilters.value = newVal as FilterOption[];
    } else {
      // Filter names - map to filter objects
      activeFilters.value = newVal.map(filterName => 
        availableFilters.value.find(f => f.name === String(filterName))
      ).filter(Boolean) as FilterOption[];
    }
  } else {
    activeFilters.value = [];
  }
}, { immediate: true });

watch(() => props.groupBy, (newVal) => {
  if (newVal !== undefined) {
    activeGroupBy.value = newVal || '';
  }
}, { immediate: true });

const defaultsApplied = ref(false);

watch(() => availableFilters.value, (newFilters) => {
  if (!defaultsApplied.value && newFilters.length > 0) {
    const defaultFilters = newFilters.filter(f => f.default);
    if (defaultFilters.length > 0) {
      activeFilters.value = defaultFilters;
      emitFilters();
    }
    defaultsApplied.value = true;
  }
}, { immediate: true });

// Initialize default filters
onMounted(() => {
  document.addEventListener('click', handleOutsideClick);
});

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick);
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.znova-search-container {
  position: relative;
  width: 100%;
}

.search-bar-main {
  position: relative;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: v.$radius-btn;
  min-height: 40px;
  transition: all 0.15s;
  
  &:focus-within {
    border-color: v.$primary-color;
  }
}

// Dark mode search bar
[data-theme="dark"] .search-bar-main {
  background: #0d1117;
  border-color: #30363d;
  
  &:focus-within {
    border-color: #2563eb;
  }
}

.search-input-wrapper {
  display: flex;
  align-items: flex-start;
  padding: 6px 12px;
  min-height: 40px;
  gap: 8px;
  width: 100%;
  
  .search-icon {
    width: 16px;
    height: 16px;
    color: v.$text-secondary;
    flex-shrink: 0;
    margin-top: 6px; /* Align with first line of content */
  }
  
  // Middle section that grows and wraps
  .search-content-wrapper {
    flex: 1;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    min-width: 0; /* Allow shrinking */
  }
  
  .inline-pills-container {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    align-items: center;
  }
  
  .search-input {
    flex: 1;
    border: none;
    outline: none;
    font-size: 0.875rem;
    color: v.$text-primary;
    background: transparent;
    min-width: 150px;
    height: 28px;
    padding: 0;
    
    &::placeholder {
      color: v.$text-placeholder;
    }
  }
  
  // Right side buttons container - stays fixed on right
  .search-actions {
    display: flex;
    align-items: center;
    gap: 0;
    flex-shrink: 0;
    align-self: stretch;
  }
  
  .search-clear {
    background: none;
    border: none;
    border-right: 1px solid v.$border-color;
    color: v.$text-secondary;
    cursor: pointer;
    padding: 0 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    height: 40px;
    margin: -6px 0 -6px -12px; /* Extend to edges */
    transition: all 0.2s;
    position: relative;
    
    // Create a pseudo-element for the background that doesn't cover the border
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 1px; /* End before the border */
      bottom: 0;
      background: transparent;
      transition: background 0.2s;
    }
    
    &:hover::before {
      background: v.$border-light;
    }
    
    &:hover {
      color: v.$text-primary;
    }
    
    &:active {
      transform: scale(0.95);
    }
    
    // Keep icon above the background
    .icon-sm {
      position: relative;
      z-index: 1;
      width: 16px;
      height: 16px;
    }
  }

// Dark mode search clear button
[data-theme="dark"] .search-input-wrapper .search-clear {
  border-right-color: #30363d;
  color: #7d8590;
  
  &:hover::before {
    background: #1c2128;
  }
  
  &:hover {
    color: #e6edf3;
  }
}
  
  .filter-toggle {
    background: none;
    border: none;
    border-left: 1px solid v.$border-color;
    color: v.$text-secondary;
    cursor: pointer;
    padding: 0 12px;
    display: flex;
    align-items: center;
    transition: all 0.2s;
    flex-shrink: 0;
    height: 40px;
    margin: -6px -12px -6px 0; /* Extend to edges */
    position: relative;
    
    // Create a pseudo-element for the background that doesn't cover the border
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 1px; /* Start after the border */
      right: 0;
      bottom: 0;
      background: transparent;
      transition: background 0.2s;
      border-radius: 0 v.$radius-btn v.$radius-btn 0; /* Round right corners only */
    }
    
    &:hover::before, &.active::before {
      background: v.$border-light;
    }
    
    &:hover, &.active {
      color: v.$primary-color;
    }
    
    // Keep icon above the background
    .icon-sm {
      position: relative;
      z-index: 1;
    }
  }
}

// Dark mode search input wrapper
[data-theme="dark"] .search-input-wrapper {
  .search-icon {
    color: #7d8590;
  }
  
  .search-input {
    color: #e6edf3;
    
    &::placeholder {
      color: #7d8590;
    }
  }
}

// Dark mode filter toggle
[data-theme="dark"] .search-input-wrapper .filter-toggle {
  border-left-color: #30363d;
  color: #7d8590;
  
  &:hover::before, &.active::before {
    background: #1c2128;
  }
  
  &:hover, &.active {
    color: #2563eb;
  }
}

.filter-pill {
  display: flex;
  align-items: center;
  background: v.$purple-600;
  color: v.$white;
  border-radius: 16px;
  padding: 3px 6px 3px 8px;
  font-size: 0.7rem;
  font-weight: 500;
  gap: 3px;
  flex-shrink: 0;
  
  &.group-by-pill {
    background: #17a2b8;
  }
  
  .pill-icon {
    font-size: 0.65rem;
  }
  
  .pill-text {
    font-weight: 600;
    white-space: nowrap;
  }
  
  .pill-remove {
    background: none;
    border: none;
    color: v.$white;
    cursor: pointer;
    padding: 1px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.8;
    transition: opacity 0.2s;
    
    &:hover {
      opacity: 1;
      background: v.$white-transparent-20;
    }
  }
}

// Dark mode filter pill - keep same colors as they're already vibrant
[data-theme="dark"] .filter-pill {
  background: #8b5cf6;
  
  &.group-by-pill {
    background: #17a2b8;
  }
}

.search-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: v.$radius-btn;
  box-shadow: 0 10px 15px -3px v.$shadow-light;
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 4px;
}

// Dark mode search suggestions
[data-theme="dark"] .search-suggestions {
  background: #161b22;
  border-color: #30363d;
}

.suggestion-item {
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: v.$text-primary;
  transition: background 0.15s;
  
  &:hover, &.active {
    background: v.$border-light;
  }
  
  .icon-xs {
    width: 14px;
    height: 14px;
    color: v.$primary-color;
    flex-shrink: 0;
  }
  
  strong {
    font-weight: 600;
    color: v.$primary-color;
  }
}

// Dark mode suggestion item
[data-theme="dark"] .suggestion-item {
  color: #e6edf3;
  
  &:hover, &.active {
    background: #1c2128;
  }
  
  .icon-xs {
    color: #2563eb;
  }
  
  strong {
    color: #2563eb;
  }
}

.filter-panel {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: v.$radius-btn;
  box-shadow: 0 10px 15px -3px v.$shadow-light;
  z-index: 1000;
  margin-top: 4px;
  min-width: 400px;
}

// Dark mode filter panel
[data-theme="dark"] .filter-panel {
  background: #161b22;
  border-color: #30363d;
}

.filter-panel-content {
  display: flex;
  min-height: 200px;
}

.filter-section {
  flex: 1;
  padding: 16px;
  
  &:not(:last-child) {
    border-right: 1px solid v.$border-light;
  }
}

// Dark mode filter section
[data-theme="dark"] .filter-section {
  &:not(:last-child) {
    border-right-color: #30363d;
  }
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid v.$border-light;
  
  .icon-sm {
    width: 16px;
    height: 16px;
    color: v.$primary-color;
  }
  
  .section-title {
    font-weight: 600;
    color: v.$text-primary;
    font-size: 0.875rem;
  }
}

// Dark mode section header
[data-theme="dark"] .section-header {
  border-bottom-color: #30363d;
  
  .icon-sm {
    color: #2563eb;
  }
  
  .section-title {
    color: #e6edf3;
  }
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  
  &:hover {
    background: v.$border-light;
  }
  
  &.active {
    background: rgba(v.$primary-color, 0.1);
    color: v.$primary-color;
    
    .filter-label {
      font-weight: 500;
    }
  }
}

// Dark mode filter option
[data-theme="dark"] .filter-option {
  &:hover {
    background: #1c2128;
  }
  
  &.active {
    background: rgba(37, 99, 235, 0.1);
    color: #2563eb;
  }
}

.filter-checkbox {
  width: 16px;
  height: 16px;
  border: 1px solid v.$border-color;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  .filter-option.active & {
    background: v.$primary-color;
    border-color: v.$primary-color;
  }
  
  .checkbox-checked {
    color: v.$white;
    font-size: 0.75rem;
    font-weight: bold;
  }
}

// Dark mode filter checkbox
[data-theme="dark"] .filter-checkbox {
  border-color: #30363d;
  
  .filter-option.active & {
    background: #2563eb;
    border-color: #2563eb;
  }
}

.filter-label {
  font-size: 0.875rem;
  color: v.$text-primary;
}

// Dark mode filter label
[data-theme="dark"] .filter-label {
  color: #e6edf3;
}

.icon-xs {
  width: 12px;
  height: 12px;
}

.icon-sm {
  width: 16px;
  height: 16px;
}

// Mobile responsiveness
@media (max-width: 768px) {
  .filter-panel {
    min-width: auto;
    left: -8px;
    right: -8px;
  }
  
  .filter-panel-content {
    flex-direction: column;
  }
  
  .filter-section {
    border-right: none;
    
    &:not(:last-child) {
      border-bottom: 1px solid v.$border-light;
    }
  }
  
  .search-input-wrapper {
    padding: 8px 12px;
    
    .inline-pills-container {
      gap: 3px;
    }
    
    .search-input {
      min-width: 80px;
    }
  }
  
  .filter-pill {
    font-size: 0.65rem;
    padding: 2px 5px 2px 6px;
    
    .pill-icon {
      font-size: 0.6rem;
    }
  }
}
</style>
