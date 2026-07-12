<template>
  <div class="datetime-container" :class="{ 'is-invalid': invalid, 'is-disabled': disabled || readonly, 'is-readonly': readonly }">
    <!-- Readonly display -->
    <div v-if="readonly" class="readonly-display">
      {{ formattedValue }}
    </div>
    
    <!-- Interactive DatePicker -->
    <DatePicker 
        v-else
        v-model="internalValue" 
        :dateFormat="primeVueDateFormat"
        :placeholder="placeholder" 
        :disabled="disabled"
        showTime
        hourFormat="12"
        @update:modelValue="handleUpdate"
        :pt="{
            root: { class: 'custom-prime-datepicker' },
            input: { class: 'custom-prime-input', style: { minHeight: touchTargetSize.minHeight } },
            panel: { class: 'custom-prime-datepicker-panel' }
        }"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import DatePicker from 'primevue/datepicker';
import Button from 'primevue/button';
import { useResponsive } from '../../composables/useResponsive';
import { formatDateTime } from '../../utils/dateUtils';

const props = defineProps<{
  modelValue: string | null;
  placeholder?: string;
  disabled?: boolean;
  invalid?: boolean;
  readonly?: boolean;
}>();

const emit = defineEmits(['update:modelValue', 'change']);

// Initialize responsive composable
const { isTouchDevice, touchTargetSize } = useResponsive();

const primeVueDateFormat = "M dd, yy"; 

const internalValue = ref<Date | null>(props.modelValue ? new Date(props.modelValue) : null);

// Computed property for formatted display value when readonly
const formattedValue = computed(() => {
  if (!props.modelValue) return '';
  
  return formatDateTime(props.modelValue);
});

watch(() => props.modelValue, (newVal) => {
  const newDate = newVal ? new Date(newVal) : null;
  if (internalValue.value?.getTime() !== newDate?.getTime()) {
      internalValue.value = newDate;
  }
});

const handleUpdate = (value: any) => {
  if (Array.isArray(value)) return; 
  
  if (!value) {
      emit('update:modelValue', null);
      emit('change', null);
      return;
  }
  
  // Return ISO string for datetime
  const isoString = value.toISOString();
  emit('update:modelValue', isoString);
  emit('change', isoString);
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.datetime-container {
  width: 100%;
  
  &.is-invalid {
    :deep(.p-inputtext) {
      border-bottom-color: v.$danger-color !important;
    }
  }
  
  &.is-readonly {
    :deep(.p-datepicker-input) {
      color: v.$text-secondary !important;
      cursor: not-allowed !important;
    }
    
    :deep(.p-datepicker-input-icon-container) {
      opacity: 0.5;
      pointer-events: none;
    }
    
    :deep(.custom-prime-datepicker) {
      cursor: not-allowed;
      pointer-events: none;
    }
  }
}

.readonly-display {
  font-size: 1rem;
  color: v.$text-primary;
  font-weight: 500;
  padding: 8px 0;
  min-height: 32px;
  display: flex;
  align-items: center;
}

:deep(.custom-prime-datepicker) {
    width: 100%;
}

:deep(.custom-prime-input),
:deep(.p-datepicker-input) {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid transparent !important;
    border-radius: 0 !important;
    padding: 0 !important;
    font-family: inherit !important;
    font-size: 1rem !important;
    color: v.$text-primary !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    height: 32px !important;
    width: 100% !important;
    cursor: text !important;
    
    &:hover {
        border-bottom-color: v.$border-color !important;
    }
    
    &:focus {
        border-bottom-color: v.$primary-color !important;
        border-bottom-width: 2px !important;
        margin-bottom: -1px;
    }

    &::placeholder {
        color: v.$text-secondary !important;
        opacity: 0.5;
    }
}

:deep(.custom-prime-datepicker) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
</style>
