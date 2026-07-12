<template>
  <div class="selection-container" ref="containerRef" :class="{ 'is-open': isOpen, 'is-invalid': invalid, 'is-disabled': disabled || readonly, 'is-readonly': readonly }">
    <div class="input-wrapper" @mousedown="handleMouseDown" :class="{ 'has-focus': hasFocus }" :style="{ minHeight: touchTargetSize.minHeight }">
      <div class="selection-display">
        {{ selectedLabel || placeholder }}
      </div>
      <div class="actions" v-if="!readonly">
        <button v-if="modelValue && !disabled" class="clear-btn" @mousedown.stop="handleClear" title="Clear" :style="{ minHeight: touchTargetSize.minHeight, minWidth: touchTargetSize.minWidth }">
          <X class="icon-sm" />
        </button>
        <button class="arrow-btn" @mousedown.stop="toggleDropdown" type="button" :title="isOpen ? 'Close' : 'Open'" :style="{ minHeight: touchTargetSize.minHeight, minWidth: touchTargetSize.minWidth }">
          <ChevronDown class="arrow-icon" :class="{ 'is-flipped': isOpen }" />
        </button>
      </div>
    </div>

    <transition name="fade">
      <div v-if="isOpen && !readonly" class="dropdown-list" ref="listRef" :style="dropdownStyle">
        <div
          v-for="(option, index) in options"
          :key="option.val"
          class="option-item"
          :class="{ 'is-focused': index === focusedIndex, 'is-selected': option.val === modelValue }"
          @mousedown.stop="selectOption(option)"
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
import { ChevronDown, X, Check } from 'lucide-vue-next';
import { useResponsive } from '../../composables/useResponsive';

const props = defineProps<{
  modelValue: any | null;
  options: Array<{ val: any, label: string }>;
  placeholder?: string;
  disabled?: boolean;
  invalid?: boolean;
  readonly?: boolean;
}>();

const emit = defineEmits(['update:modelValue', 'change']);

// Initialize responsive composable
const { isTouchDevice, touchTargetSize } = useResponsive();

const isOpen = ref(false);
const hasFocus = ref(false);
const focusedIndex = ref(-1);
const containerRef = ref<HTMLElement | null>(null);
const listRef = ref<HTMLElement | null>(null);

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

watch(isOpen, (val) => {
  if (val) {
    if (props.options) {
      focusedIndex.value = props.options.findIndex(opt => opt.val === props.modelValue);
      if (focusedIndex.value === -1 && props.options.length > 0) {
        focusedIndex.value = 0;
      }
    }
    // Multiple attempts to ensure proper positioning
    nextTick(() => {
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
    focusedIndex.value = -1;
  }
});

const toggleDropdown = () => {
    if (props.disabled || props.readonly) return;
    isOpen.value = !isOpen.value;
    if (isOpen.value) hasFocus.value = true;
};

const handleMouseDown = (e: MouseEvent) => {
  if (props.disabled || props.readonly) return;
  if ((e.target as HTMLElement).closest('.actions')) return;

  isOpen.value = !isOpen.value;
  hasFocus.value = true;
};

const selectOption = (option: { val: any, label: string } | null) => {
  emit('update:modelValue', option ? option.val : null);
  emit('change', option ? option.val : null);
  isOpen.value = false;
  hasFocus.value = false;
};

const handleClear = () => {
  selectOption(null);
};

const handleClickOutside = (e: MouseEvent) => {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    isOpen.value = false;
    hasFocus.value = false;
  }
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
@use "../../styles/variables" as v;

.selection-container {
  position: relative;
  width: 100%;
  font-family: inherit;

  &.is-disabled {
    pointer-events: none;
    opacity: 0.7;
  }

  &.is-readonly {
    .input-wrapper {
      cursor: not-allowed;
      
      .selection-display {
        color: v.$text-secondary !important;
      }
      
      &:hover {
        border-bottom-color: transparent !important;
      }
    }
  }

  &.is-invalid {
    .input-wrapper {
      border-bottom-color: v.$danger-color !important;
      
      .selection-display {
        color: v.$danger-color;
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
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0;
  height: 32px;
  background: transparent;
  border-bottom: 1px solid transparent;
  cursor: pointer;
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
    .actions { 
        opacity: 1 !important;
        visibility: visible !important;
    }
  }
}

.selection-display {
  flex: 1;
  font-size: 1rem;
  color: v.$text-primary;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  position: relative;
  z-index: 1;
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

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.1s, transform 0.1s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

.icon-sm {
  width: 14px;
  height: 14px;
}

// Dark mode styles
[data-theme="dark"] {
  .selection-container {
    &.is-readonly {
      .input-wrapper {
        .selection-display {
          color: #7d8590 !important;
        }
      }
    }
    
    &.is-invalid {
      .input-wrapper {
        border-bottom-color: #f85149 !important;
        
        .selection-display {
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
  
  .selection-display {
    color: #e6edf3;
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
}
</style>
