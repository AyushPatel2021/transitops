<template>
  <div class="many2many-container" ref="containerRef" :class="{ 'is-open': isOpen, 'is-invalid': invalid, 'is-disabled': disabled || readonly, 'is-readonly': readonly }">
    <div class="input-wrapper" @mousedown="handleMouseDown" :class="{ 'has-focus': hasFocus }">
      <!-- Selected pills -->
      <div class="pills-container" v-if="modelValue.length > 0">
        <div 
          v-for="id in modelValue" 
          :key="id" 
          class="pill"
        >
          <span class="pill-text">{{ getRecordName(id) }}</span>
            <button
              v-if="!readonly"
              @mousedown.stop.prevent="removeSelection(id)"
              class="pill-remove"
              type="button"
              title="Remove"
            >
            <X :size="14" />
          </button>
        </div>
      </div>
      
      <!-- Input field -->
      <input
        type="text"
        ref="inputRef"
        v-model="searchQuery"
        class="many2many-input"
        :placeholder="modelValue.length === 0 ? placeholder : ''"
        :disabled="disabled || readonly"
        @keydown="handleKeyDown"
        @blur="handleBlur"
        @focus="handleFocus"
      />
      
      <!-- Dropdown arrow -->
      <div class="actions" v-if="!readonly">
        <button class="arrow-btn" @mousedown.stop.prevent="toggleDropdown" type="button" :title="isOpen ? 'Close' : 'Open'">
          <ChevronDown class="arrow-icon" :class="{ 'is-flipped': isOpen }" />
        </button>
      </div>
    </div>

    <!-- Dropdown list -->
    <transition name="fade">
      <div v-if="isOpen && !readonly" class="dropdown-list" ref="listRef" :style="dropdownStyle">
        <div v-if="loading" class="loading-state">
          Loading...
        </div>
        <div v-else-if="filteredOptions.length === 0" class="no-options">
          No results found
        </div>
        <div
          v-else
          v-for="(option, index) in filteredOptions"
          :key="option.id"
          class="option-item"
          :class="{ 'is-focused': index === focusedIndex, 'is-selected': modelValue.includes(option.id) }"
          @mousedown.stop.prevent="selectOption(option)"
          @mouseenter="focusedIndex = index"
        >
          <Check v-if="modelValue.includes(option.id)" class="check-icon" />
          <span class="label">{{ getRecordDisplayName(option) }}</span>
        </div>
      </div>
    </transition>
    
    <!-- Validation error -->
    <div v-if="invalid && showValidationError" class="validation-error">
      <AlertCircle :size="16" />
      <span>This field is required</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { X, ChevronDown, Check, AlertCircle } from 'lucide-vue-next';
import api from '../../core/api';
import { DomainEngine } from '../../core/domain-engine';

interface Many2manyMetadata {
  relation: string;
  relation_table?: string;
  display_format?: string;
  searchable?: boolean;
  create_inline?: boolean;
  domain?: string;
  required?: boolean;
  label?: string;
  [key: string]: any;
}

interface RelatedRecord {
  id: number;
  name?: string;
  full_name?: string;
  subject?: string;
  [key: string]: any;
}

const props = withDefaults(defineProps<{
  modelValue: number[];
  metadata: Many2manyMetadata;
  readonly?: boolean;
  invalid?: boolean;
  disabled?: boolean;
  context?: Record<string, any>;
}>(), {
  context: () => ({})
});

const emit = defineEmits(['update:modelValue', 'error']);

// Local state
const isOpen = ref(false);
const searchQuery = ref('');
const focusedIndex = ref(-1);
const containerRef = ref<HTMLElement | null>(null);
const inputRef = ref<HTMLInputElement | null>(null);
const listRef = ref<HTMLElement | null>(null);
const hasFocus = ref(false);
const loading = ref(false);
const availableRecords = ref<RelatedRecord[]>([]);
const selectedRecords = ref<Map<number, RelatedRecord>>(new Map());
const showValidationError = ref(false);
const dropdownStyle = ref({});

// Computed
const placeholder = computed(() => props.metadata.label || 'Select items...');

const filteredOptions = computed(() => {
  let options = availableRecords.value;
  
  if (searchQuery.value && props.metadata.searchable !== false) {
    const q = searchQuery.value.toLowerCase();
    options = options.filter(record => {
      const name = getRecordDisplayName(record).toLowerCase();
      return name.includes(q);
    });
  }
  
  return options;
});

// Methods
const getRecordDisplayName = (record: RelatedRecord): string => {
  const recName = props.metadata?.rec_name || 'display_name';
  return record[recName] || record.display_name || record.name || record.full_name || record.subject || `#${record.id}`;
};

const getRecordName = (id: number): string => {
  const record = selectedRecords.value.get(id);
  if (record) {
    return getRecordDisplayName(record);
  }
  
  const availableRecord = availableRecords.value.find(r => r.id === id);
  if (availableRecord) {
    return getRecordDisplayName(availableRecord);
  }
  
  return `#${id}`;
};

const loadAvailableOptions = async (silent = false) => {
  if (!props.metadata.relation) {
    emit('error', 'Many2many field missing relation metadata');
    return;
  }
  
  if (!silent) loading.value = true;
  try {
    const params: any = {};
    
    if (props.metadata.domain) {
      try {
        const domainEngine = new DomainEngine();
        // Use resolveDomain to handle both static and dynamic domains (with variables)
        const domainFilters = domainEngine.resolveDomain(props.metadata.domain, props.context);
        
        if (domainFilters && domainFilters.length > 0) {
          params.domain = JSON.stringify(domainFilters);
        }
      } catch (e) {
        // Silently handle domain processing errors
      }
    }
    
    const response = await api.get(`/models/${props.metadata.relation}`, { params });
    availableRecords.value = response.data?.items || [];
  } catch (error) {
    emit('error', `Failed to load options for ${props.metadata.relation}`);
    availableRecords.value = [];
  } finally {
    loading.value = false;
  }
};

const loadSelectedRecords = async () => {
  if (!props.modelValue || props.modelValue.length === 0) {
    selectedRecords.value.clear();
    return;
  }
  
  if (!props.metadata.relation) return;
  
  try {
    const response = await api.get(`/models/${props.metadata.relation}`, {
      params: {
        filters: JSON.stringify([['id', 'in', props.modelValue]])
      }
    });
    
    const records = response.data?.items || [];
    selectedRecords.value.clear();
    records.forEach((record: RelatedRecord) => {
      selectedRecords.value.set(record.id, record);
    });
  } catch (error) {
    // Silently handle loading errors
  }
};

const updateDropdownPosition = () => {
  if (!containerRef.value || !isOpen.value) {
    return;
  }
  
  nextTick(() => {
    const rect = containerRef.value!.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const dropdownHeight = 250;
    
    if (rect.top === 0 && rect.left === 0 && rect.width === 0) {
      dropdownStyle.value = {
        position: 'absolute',
        top: 'calc(100% + 4px)',
        left: '0',
        right: '0',
        zIndex: 9999
      };
      return;
    }
    
    const spaceBelow = viewportHeight - rect.bottom;
    const spaceAbove = rect.top;
    const openUpward = spaceBelow < dropdownHeight && spaceAbove > spaceBelow;
    
    const newStyle = {
      position: 'fixed',
      left: `${rect.left}px`,
      width: `${rect.width}px`,
      zIndex: 9999,
      ...(openUpward 
        ? { bottom: `${viewportHeight - rect.top}px` }
        : { top: `${rect.bottom + 4}px` }
      )
    };
    
    dropdownStyle.value = newStyle;
  });
};

const toggleDropdown = () => {
  if (props.readonly || props.disabled) return;
  
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    nextTick(() => {
      inputRef.value?.focus();
      updateDropdownPosition();
    });
  }
};

const selectOption = (option: RelatedRecord) => {
  if (props.modelValue.includes(option.id)) {
    // Remove if already selected
    const newValue = props.modelValue.filter(id => id !== option.id);
    selectedRecords.value.delete(option.id);
    emit('update:modelValue', newValue);
  } else {
    // Add if not selected
    const newValue = [...props.modelValue, option.id];
    selectedRecords.value.set(option.id, option);
    emit('update:modelValue', newValue);
  }
  
  // Keep dropdown open and reset search
  searchQuery.value = '';
  focusedIndex.value = -1;
  
  // Refocus input
  nextTick(() => {
    inputRef.value?.focus();
  });
};

const removeSelection = (id: number) => {
  const newValue = props.modelValue.filter(selectedId => selectedId !== id);
  selectedRecords.value.delete(id);
  emit('update:modelValue', newValue);
};

const handleMouseDown = (e: MouseEvent) => {
  // Stop event propagation to prevent interference
  e.stopPropagation();
  
  if (props.readonly || props.disabled) return;
  
  // Don't action if clicking on a pill remove button
  if ((e.target as HTMLElement).closest('.pill-remove')) {
    return;
  }
  
  if (!isOpen.value) {
    isOpen.value = true;
    nextTick(() => {
      inputRef.value?.focus();
      updateDropdownPosition();
    });
  } else {
    // If already open, just make sure input keeps focus
    e.preventDefault();
    inputRef.value?.focus();
  }
};

const handleFocus = () => {
  hasFocus.value = true;
  if (!isOpen.value) {
    isOpen.value = true;
    updateDropdownPosition();
  }
};

const handleBlur = () => {
  hasFocus.value = false;
  // Delay closing to allow click events to fire
  setTimeout(() => {
    // Only close if focus hasn't moved somewhere else within the container
    if (!containerRef.value?.contains(document.activeElement)) {
      isOpen.value = false;
      searchQuery.value = '';
    }
  }, 200);
};

const handleKeyDown = (e: KeyboardEvent) => {
  if (!isOpen.value && (e.key === 'ArrowDown' || e.key === 'Enter')) {
    isOpen.value = true;
    updateDropdownPosition();
    e.preventDefault();
    return;
  }

  if (!isOpen.value) return;

  switch (e.key) {
    case 'ArrowDown':
      if (filteredOptions.value.length === 0) return;
      focusedIndex.value = (focusedIndex.value + 1) % filteredOptions.value.length;
      scrollToFocused();
      e.preventDefault();
      break;
    case 'ArrowUp':
      if (filteredOptions.value.length === 0) return;
      focusedIndex.value = (focusedIndex.value - 1 + filteredOptions.value.length) % filteredOptions.value.length;
      scrollToFocused();
      e.preventDefault();
      break;
    case 'Enter':
      if (focusedIndex.value >= 0 && focusedIndex.value < filteredOptions.value.length) {
        selectOption(filteredOptions.value[focusedIndex.value]);
      }
      e.preventDefault();
      break;
    case 'Escape':
      isOpen.value = false;
      searchQuery.value = '';
      e.preventDefault();
      break;
    case 'Tab':
      isOpen.value = false;
      break;
    case 'Backspace':
      // Remove last pill if input is empty
      if (searchQuery.value === '' && props.modelValue.length > 0) {
        const lastId = props.modelValue[props.modelValue.length - 1];
        removeSelection(lastId);
        e.preventDefault();
      }
      break;
  }
};

const scrollToFocused = () => {
  nextTick(() => {
    const list = listRef.value;
    if (!list) return;
    const item = list.children[focusedIndex.value] as HTMLElement;
    if (!item) return;

    const listRect = list.getBoundingClientRect();
    const itemRect = item.getBoundingClientRect();

    if (itemRect.bottom > listRect.bottom) {
      list.scrollTop += (itemRect.bottom - listRect.bottom);
    } else if (itemRect.top < listRect.top) {
      list.scrollTop -= (listRect.top - itemRect.top);
    }
  });
};

const handleClickOutside = (e: MouseEvent) => {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    isOpen.value = false;
    searchQuery.value = '';
  }
};

watch(() => props.modelValue, () => {
  loadSelectedRecords();
  // Update dropdown position as pills change the field height
  if (isOpen.value) {
    nextTick(() => {
      updateDropdownPosition();
    });
  }
}, { immediate: true, deep: true });

watch(() => props.invalid, (val) => {
  if (val && props.metadata.required) {
    showValidationError.value = true;
  }
});

watch(() => props.context, (newContext, oldContext) => {
  // Only reload if the domain contains variables that might have changed
  // and do it silently to avoid blinking
  if (props.metadata.domain && props.metadata.domain.includes('(')) {
    loadAvailableOptions(true);
  }
}, { deep: true });

watch(isOpen, (val) => {
  if (val) {
    focusedIndex.value = -1;
    // Always reload options when opening if there is a domain, to ensure they are fresh
    if (props.metadata.domain) {
      loadAvailableOptions();
    }
    updateDropdownPosition();
    window.addEventListener('scroll', updateDropdownPosition, true);
    window.addEventListener('resize', updateDropdownPosition);
  } else {
    window.removeEventListener('scroll', updateDropdownPosition, true);
    window.removeEventListener('resize', updateDropdownPosition);
  }
});

onMounted(() => {
  loadAvailableOptions();
  loadSelectedRecords();
  document.addEventListener('mousedown', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside);
  window.removeEventListener('scroll', updateDropdownPosition, true);
  window.removeEventListener('resize', updateDropdownPosition);
});

defineExpose({
  validate: () => {
    if (props.metadata.required && props.modelValue.length === 0) {
      showValidationError.value = true;
      return false;
    }
    showValidationError.value = false;
    return true;
  }
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.many2many-container {
  position: relative;
  width: 100%;
  font-family: inherit;

  &.is-disabled {
    pointer-events: none;
    opacity: 0.7;
    .input-wrapper {
      background: transparent;
    }
  }

  &.is-readonly {
    .input-wrapper {
      cursor: not-allowed;
      
      .many2many-input {
        color: v.$text-secondary !important;
        cursor: not-allowed !important;
      }
      
      &:hover {
        border-bottom-color: transparent !important;
      }
    }
  }

  &.is-invalid {
    .input-wrapper {
      border-bottom-color: v.$danger-color !important;
      
      .many2many-input {
        color: v.$danger-color;
        
        &::placeholder {
          color: v.$danger-color;
        }
      }
      
      &:hover {
        border-bottom-color: v.$danger-color !important;
      }
      
      &.has-focus {
        border-bottom-color: v.$danger-color !important;
      }
    }
  }
}

.input-wrapper {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  min-height: 32px;
  background: transparent;
  border-bottom: 1px solid transparent;
  border-radius: 0;
  cursor: text;
  transition: all 0.2s ease;

  &:hover {
    border-bottom-color: v.$border-color;
    
    .actions {
      opacity: 1 !important;
      visibility: visible !important;
    }
  }

  &.has-focus {
    border-bottom-color: v.$primary-color !important;
    border-bottom-width: 2px;
    margin-bottom: -1px;
    background: transparent;

    .actions {
      opacity: 1 !important;
      visibility: visible !important;
    }
  }
}

.pills-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  background: rgba(v.$primary-color, 0.1);
  border: 1px solid rgba(v.$primary-color, 0.3);
  border-radius: 12px; /* Rounded pills */
  font-size: 0.85rem;
  color: v.$primary-color;
  max-width: 200px;
  font-weight: 500;
  
  .pill-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .pill-remove {
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    color: v.$primary-color;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.15s;
    
    &:hover {
      background: rgba(v.$primary-color, 0.2);
      color: v.$danger-color;
    }
  }
}

// Dark mode pill
[data-theme="dark"] .pill {
  background: rgba(37, 99, 235, 0.15);
  border-color: rgba(37, 99, 235, 0.4);
  color: #58a6ff;
  
  .pill-remove {
    color: #58a6ff;
    
    &:hover {
      background: rgba(37, 99, 235, 0.25);
      color: #f85149;
    }
  }
}

.many2many-input {
  flex: 1;
  min-width: 120px;
  height: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 1rem;
  color: v.$text-primary;
  font-weight: 500;
  cursor: text;
  padding: 0;
  
  &::placeholder {
    color: v.$text-secondary;
    font-weight: 400;
  }
  
  &:disabled {
    cursor: not-allowed;
  }
}

.actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: v.$text-secondary;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s;
  position: relative;
  z-index: 3;
}

.arrow-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: v.$text-secondary;
  transition: all 0.2s;
  
  &:hover {
    background: v.$overlay-light;
    color: v.$primary-color;
  }
  
  .arrow-icon {
    width: 14px;
    height: 14px;
    transition: transform 0.2s;
    
    &.is-flipped {
      transform: rotate(180deg);
    }
  }
}

.dropdown-list {
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px v.$shadow-color-md;
  max-height: 250px;
  overflow-y: auto;
  padding: 4px 0;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: v.$border-color;
    border-radius: 10px;
  }
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0.6rem 1rem;
  cursor: pointer;
  transition: all 0.1s;
  font-size: 0.9rem;
  color: v.$text-primary;
  
  &.is-focused {
    background: v.$bg-main;
    color: v.$primary-color;
  }
  
  &.is-selected {
    font-weight: 600;
    color: v.$primary-color;
    background: rgba(v.$primary-color, 0.05);
  }
  
  .check-icon {
    width: 14px;
    height: 14px;
    color: v.$primary-color;
    flex-shrink: 0;
  }
  
  .label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.loading-state,
.no-options {
  padding: 1rem;
  text-align: center;
  color: v.$text-secondary;
  font-size: 0.85rem;
  font-style: italic;
}

.validation-error {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  padding: 6px 10px;
  background: v.$light-red-bg;
  border: 1px solid v.$light-red-border;
  border-radius: 4px;
  color: v.$red-text;
  font-size: 13px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.1s, transform 0.1s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

// Dark mode styles
[data-theme="dark"] {
  .many2many-container {
    &.is-readonly {
      .input-wrapper {
        .many2many-input {
          color: #7d8590 !important;
        }
      }
    }
    
    &.is-invalid {
      .input-wrapper {
        border-bottom-color: #f85149 !important;
        
        .many2many-input {
          color: #f85149;
        }
        
        &:hover, &.has-focus {
          border-bottom-color: #f85149 !important;
        }
      }
    }
  }
  
  .input-wrapper {
    &:hover {
      border-bottom-color: #30363d;
    }
    
    &.has-focus {
      border-bottom-color: #58a6ff !important;
    }
  }
  
  .many2many-input {
    color: #e6edf3;
    
    &::placeholder {
      color: #7d8590;
    }
  }
  
  .actions {
    color: #7d8590;
    
    .clear-btn, .arrow-btn {
      color: #7d8590;
      
      &:hover {
        background: rgba(110, 118, 129, 0.1);
        color: #58a6ff;
      }
    }
    
    .clear-btn:hover {
      color: #f85149;
    }
  }
  
  .dropdown-list {
    background: #161b22;
    border-color: #30363d;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    
    &::-webkit-scrollbar-thumb {
      background: #30363d;
      
      &:hover {
        background: #484f58;
      }
    }
  }
  
  .option-item {
    color: #e6edf3;
    
    &.is-focused {
      background: #0d1117;
      color: #58a6ff;
    }
    
    &.is-selected {
      color: #58a6ff;
      background: rgba(88, 166, 255, 0.1);
    }
    
    .check-icon {
      color: #58a6ff;
    }
  }
  
  .loading-state,
  .no-options {
    color: #7d8590;
  }
  
  .validation-error {
    background: rgba(248, 81, 73, 0.1);
    border-color: rgba(248, 81, 73, 0.3);
    color: #f85149;
  }
}
</style>
