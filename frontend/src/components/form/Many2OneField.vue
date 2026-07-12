<template>
  <div class="many2one-container" ref="containerRef" :class="{ 'is-open': isOpen, 'is-invalid': invalid, 'is-disabled': disabled || readonly, 'is-readonly': readonly }">
    <div class="input-wrapper" @mousedown="handleMouseDown" :class="{ 'has-focus': hasFocus }" :style="{ minHeight: touchTargetSize.minHeight }">
      <div 
        class="selected-display" 
        :class="{ 'is-hidden': hasFocus || (isOpen && searchQuery) || !selectedLabel, 'is-clickable': readonly && modelValue }" 
        @click="handleDisplayClick"
      >
        {{ selectedLabel }}
      </div>
      <input
        type="text"
        ref="inputRef"
        v-model="searchQuery"
        class="many2one-input"
        :placeholder="selectedLabel ? '' : placeholder"
        :disabled="disabled || readonly"
        @keydown="handleKeyDown"
        @blur="handleBlur"
        @focus="handleFocus"
        :style="{ minHeight: touchTargetSize.minHeight }"
      />
      <div class="actions" v-if="!readonly">
        <button v-if="modelValue && !disabled" class="clear-btn" @mousedown.stop="handleClear" title="Clear" :style="{ minHeight: touchTargetSize.minHeight, minWidth: touchTargetSize.minWidth }">
          <X class="icon-sm" />
        </button>
        <button v-if="modelValue && !disabled" class="open-record-btn" @click.stop="handleOpenRecord" title="Open Record" :style="{ minHeight: touchTargetSize.minHeight, minWidth: touchTargetSize.minWidth }">
          <ExternalLink class="icon-sm" />
        </button>
        <button class="arrow-btn" @mousedown.stop="toggleDropdown" type="button" :title="isOpen ? 'Close' : 'Open'" :style="{ minHeight: touchTargetSize.minHeight, minWidth: touchTargetSize.minWidth }">
          <ChevronDown class="arrow-icon" :class="{ 'is-flipped': isOpen }" />
        </button>
      </div>
    </div>

    <transition name="fade">
      <div v-if="isOpen && !readonly" class="dropdown-list" ref="listRef" :style="dropdownStyle">
        <div v-if="filteredOptions.length === 0" class="no-options" @click.stop>
          No results found
        </div>
        <div
          v-for="(option, index) in filteredOptions"
          :key="option.val"
          class="option-item"
          :class="{ 'is-focused': index === focusedIndex, 'is-selected': option.val === modelValue }"
          @click="selectOption(option)"
          @mouseenter="focusedIndex = index"
          :style="{ minHeight: touchTargetSize.minHeight }"
        >
          <span class="label">{{ option.label }}</span>
          <Check v-if="option.val === modelValue" class="check-icon" />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { ChevronDown, X, Check, ExternalLink } from 'lucide-vue-next';
import { useResponsive } from '../../composables/useResponsive';
import { useRouter } from 'vue-router';

const props = defineProps<{
  modelValue: any | null;
  options: Array<{ val: any, label: string }>;
  placeholder?: string;
  disabled?: boolean;
  invalid?: boolean;
  readonly?: boolean;
  relation?: string; // The related model name (e.g., 'res.partner')
}>();

const emit = defineEmits(['update:modelValue', 'focus', 'change']);

// Initialize responsive composable
const { isTouchDevice, touchTargetSize } = useResponsive();
const router = useRouter();

const isOpen = ref(false);
const searchQuery = ref('');
const focusedIndex = ref(-1);
const containerRef = ref<HTMLElement | null>(null);
const inputRef = ref<HTMLInputElement | null>(null);
const listRef = ref<HTMLElement | null>(null);

const hasFocus = ref(false);
const userClearedText = ref(false); // Track if user manually cleared the text

// Dropdown positioning
const dropdownStyle = ref({});

const updateDropdownPosition = () => {
  if (!containerRef.value || !isOpen.value) {
    return;
  }
  
  // Wait for next tick to ensure DOM is fully rendered
  nextTick(() => {
    const rect = containerRef.value!.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const dropdownHeight = 250; // max-height of dropdown
    
    // Check if we got valid positioning data
    if (rect.top === 0 && rect.left === 0 && rect.width === 0) {
      // Fallback to absolute positioning
      dropdownStyle.value = {
        position: 'absolute',
        top: 'calc(100% + 4px)',
        left: '0',
        right: '0',
        zIndex: 9999
      };
      return;
    }
    
    // Calculate if dropdown should open upward or downward
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

const selectedLabel = computed(() => {
  if (!props.options) return '';
  const selected = props.options.find(opt => opt.val === props.modelValue);
  return selected ? selected.label : '';
});

const filteredOptions = computed(() => {
  if (!props.options) return [];
  if (!searchQuery.value) return props.options;
  const q = searchQuery.value.toLowerCase();
  return props.options.filter(opt => 
    opt.label.toLowerCase().includes(q)
  );
});

watch(isOpen, (val) => {
  if (val) {
    searchQuery.value = selectedLabel.value;
    userClearedText.value = false; // Reset the flag when opening
    focusedIndex.value = filteredOptions.value.findIndex(opt => opt.val === props.modelValue);
    if (focusedIndex.value === -1 && filteredOptions.value.length > 0) {
      focusedIndex.value = 0;
    }
    nextTick(() => {
        inputRef.value?.select();
        // Multiple attempts to ensure proper positioning
        updateDropdownPosition();
        // Additional delay for first load issues
        setTimeout(() => {
          updateDropdownPosition();
        }, 10);
        // Final fallback
        setTimeout(() => {
          updateDropdownPosition();
        }, 100);
    });
  } else {
    // When closing, always clear searchQuery to show selected-display
    searchQuery.value = '';
    userClearedText.value = false; // Reset flag
    focusedIndex.value = -1;
  }
});

// Watch searchQuery to detect when user manually clears it
watch(searchQuery, (newVal, oldVal) => {
  // If user had text and now it's empty, they cleared it
  if (isOpen.value && oldVal && oldVal.length > 0 && newVal.trim() === '') {
    userClearedText.value = true;
  }
});

const toggleDropdown = () => {
    if (props.disabled || props.readonly) return;
    if (isOpen.value) {
        isOpen.value = false;
        inputRef.value?.blur();
    } else {
        isOpen.value = true;
        emit('focus');
        nextTick(() => {
            inputRef.value?.focus();
            inputRef.value?.select();
        });
    }
};

const handleMouseDown = (e: MouseEvent) => {
  // Prevent default to avoid text selection issues
  e.preventDefault();
  e.stopPropagation();
  
  if (props.disabled || props.readonly) return;
  
  // If clicking an action button, let its own handler deal with it
  if ((e.target as HTMLElement).closest('.actions')) {
    return;
  }

  // Always focus the input and select text for easy editing
  if (!isOpen.value) {
    isOpen.value = true;
    emit('focus');
  }
  
  nextTick(() => {
    inputRef.value?.focus();
    // Always select all text when clicking the field
    inputRef.value?.select();
  });
};

const handleFocus = () => {
  hasFocus.value = true;
  emit('focus');
  
  // Auto-select text when focusing for easier editing
  nextTick(() => {
    if (inputRef.value && selectedLabel.value) {
      inputRef.value.select();
    }
  });
};

const handleBlur = () => {
    hasFocus.value = false;
    
    // Only clear the selection if user manually cleared ALL the text
    if (userClearedText.value && searchQuery.value.trim() === '') {
        // Clear the value immediately to prevent blink
        emit('update:modelValue', null);
        emit('change', null);
    }
    
    // Longer delay to allow click events on the dropdown items to proceed properly
    setTimeout(() => {
        // Check if focus is still within the component or if user clicked on dropdown
        if (!containerRef.value?.contains(document.activeElement) && 
            !containerRef.value?.querySelector('.dropdown-list:hover')) {
            isOpen.value = false;
        }
    }, 150);
};

const selectOption = (option: { val: any, label: string } | null) => {
  // Prevent event bubbling that might interfere with selection
  event?.stopPropagation();
  
  emit('update:modelValue', option ? option.val : null);
  emit('change', option ? option.val : null);
  isOpen.value = false;
  inputRef.value?.blur();
};

const handleClear = () => {
  selectOption(null);
};

const handleKeyDown = (e: KeyboardEvent) => {
  if (!isOpen.value) {
    if (e.key === 'ArrowDown' || e.key === 'Enter') {
      isOpen.value = true;
      e.preventDefault();
    }
    return;
  }

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
      inputRef.value?.blur();
      e.preventDefault();
      break;
    case 'Tab':
      isOpen.value = false;
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
  }
};

const handleDisplayClick = () => {
  console.log('Display clicked!', { 
    readonly: props.readonly, 
    modelValue: props.modelValue, 
    relation: props.relation,
    selectedLabel: selectedLabel.value 
  });
  
  if (props.readonly && props.modelValue) {
    handleOpenRecord();
  }
};

const handleOpenRecord = () => {
  console.log('handleOpenRecord called', { 
    modelValue: props.modelValue, 
    relation: props.relation 
  });
  
  if (!props.modelValue || !props.relation) {
    console.log('Cannot open record:', { modelValue: props.modelValue, relation: props.relation });
    return;
  }
  
  console.log('Opening record:', { relation: props.relation, id: props.modelValue });
  
  // Navigate to the related record
  router.push(`/models/${props.relation}/${props.modelValue}`);
};

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside);
  window.addEventListener('resize', updateDropdownPosition);
  window.addEventListener('scroll', updateDropdownPosition, true);
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside);
  window.removeEventListener('resize', updateDropdownPosition);
  window.removeEventListener('scroll', updateDropdownPosition, true);
});
</script>

<style lang="scss" scoped>
@use "sass:color";
@use "../../styles/variables" as v;

.many2one-container {
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
      
      .selected-display {
        color: v.$text-secondary !important;
        
        /* Override for clickable many2one links */
        &.is-clickable {
          color: v.$link-color !important;
          cursor: pointer !important;
          
          &:hover {
            color: v.$link-hover !important;
          }
        }
      }
      
      .many2one-input {
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
      
      .selected-display {
        color: v.$danger-color;
      }
      
      .many2one-input {
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
  gap: 0.5rem;
  height: 32px; // Slimmer 
  background: transparent;
  border-bottom: 1px solid transparent; // Only underline
  border-radius: 0; // No rounded corners for underline style
  cursor: text;
  transition: all 0.2s ease;
  position: relative; // Added to contain absolute positioned actions

  &:hover {
    border-bottom-color: v.$border-color;
    
    .actions {
        opacity: 1 !important;
        visibility: visible !important;
    }
  }

  &.has-focus {
    border-bottom-color: v.$primary-color !important;
    border-bottom-width: 2px; // Thicker underline when focused
    margin-bottom: -1px; // Offset for thicker border
    background: transparent;

    .actions {
        opacity: 1 !important;
        visibility: visible !important;
    }
  }
}

.selected-display {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: calc(100% - 100px); /* Increased space for 3 buttons */
  display: flex;
  align-items: center;
  font-size: 1rem;
  color: v.$text-primary;
  font-weight: 500;
  background: transparent;
  pointer-events: none;
  z-index: 1;
  transition: all 0.2s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 8px; /* Additional padding to prevent overlap */

  &.is-hidden {
    opacity: 0;
    pointer-events: none;
  }
  
  &.is-clickable {
    color: v.$link-color;
    cursor: pointer;
    pointer-events: auto;
    width: auto; /* Only text width, not full width */
    z-index: 3; /* Above the input */
    
    &:hover {
      color: v.$link-hover;
    }
  }
}

.many2one-input {
  flex: 1;
  height: 100%;
  border: none;
  outline: none;
  background: transparent;
  width: 100%;
  font-size: 1rem;
  color: v.$text-primary;
  font-weight: 500;
  cursor: text;
  padding: 0;
  position: relative;
  z-index: 1;
  
  // Ensure the input doesn't show its own value/placeholder when overlay is active
  &::placeholder {
    color: transparent;
  }
}

.actions {
  display: flex;
  align-items: center;
  gap: 0.2rem; // Reduced gap
  color: v.$text-secondary;
  opacity: 0; // Hidden by default
  visibility: hidden;
  transition: all 0.2s;
  position: absolute; // Changed to absolute positioning
  right: 0; // Align to right edge
  top: 0;
  height: 100%;
  z-index: 3;
  background: transparent; // Ensure no background interference
  padding-left: 8px; // Add some padding to create separation from text

  .clear-btn, .arrow-btn {
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
  }

  .clear-btn:hover {
      color: v.$danger-color;
  }
  
  .open-record-btn {
    background: none;
    border: none;
    padding: 4px;
    cursor: pointer;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: v.$primary-color;
    transition: all 0.2s;
    
    &:hover {
      background: v.$overlay-light;
      color: v.$primary-hover;
    }
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
  /* Position will be set dynamically via JavaScript */
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px v.$shadow-color-md;
  max-height: 250px;
  overflow-y: auto;
  padding: 4px 0;
  user-select: none; /* Prevent text selection issues */

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
  justify-content: space-between;
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
  }
}

.no-options {
  padding: 1rem;
  text-align: center;
  color: v.$text-secondary;
  font-size: 0.85rem;
  font-style: italic;
}

.icon-sm {
  width: 14px;
  height: 14px;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.1s, transform 0.1s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

// Dark mode styles
[data-theme="dark"] {
  .many2one-container {
    &.is-readonly {
      .input-wrapper {
        .display-value {
          color: #7d8590 !important;
        }
      }
    }
    
    &.is-invalid {
      .input-wrapper {
        border-bottom-color: #f85149 !important;
        
        .display-value, .many2one-input {
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
  
  .display-value, .many2one-input {
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
  }
  
  .no-options {
    color: #7d8590;
  }
}
</style>
