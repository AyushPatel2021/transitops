<template>
  <div class="date-container" :class="{ 'is-invalid': invalid, 'is-disabled': disabled || readonly, 'is-readonly': readonly }">
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
        showButtonBar
        :showTime="showTime"
        :hourFormat="hourFormat"
        @update:modelValue="handleUpdate"
        :pt="{
            root: { class: 'custom-prime-datepicker' },
            input: { class: 'custom-prime-input', style: { minHeight: touchTargetSize.minHeight } },
            panel: { class: 'custom-prime-datepicker-panel' }
        }"
    >
      <template #buttonbar="{ todayCallback, clearCallback }">
        <div class="custom-buttonbar">
          <Button label="Today" text size="small" @click="todayCallback" class="p-0" />
          <Button label="Clear" text size="small" severity="secondary" @click="clearCallback" class="p-0" />
        </div>
      </template>
    </DatePicker>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import DatePicker from 'primevue/datepicker';
import Button from 'primevue/button';
import { useResponsive } from '../../composables/useResponsive';
import { formatDateTime, formatDate } from '../../utils/dateUtils';

const props = withDefaults(defineProps<{
  modelValue: string | null;
  placeholder?: string;
  disabled?: boolean;
  invalid?: boolean;
  readonly?: boolean;
  showTime?: boolean;
  hourFormat?: '12' | '24';
}>(), {
  showTime: false,
  hourFormat: '12'
});

const emit = defineEmits(['update:modelValue', 'change']);

// Initialize responsive composable
const { isTouchDevice, touchTargetSize } = useResponsive();

// PrimeVue uses different format tokens: yy for 4-digit year, mm for 2-digit month, dd for 2-digit day
const primeVueDateFormat = "M dd, yy"; 

const internalValue = ref<Date | null>(props.modelValue ? new Date(props.modelValue) : null);

// Computed property for formatted display value when readonly
const formattedValue = computed(() => {
  if (!props.modelValue) return '';
  
  if (props.showTime) {
    // Format datetime
    return formatDateTime(props.modelValue);
  } else {
    // Format date only
    return formatDate(props.modelValue);
  }
});

watch(() => props.modelValue, (newVal) => {
  const newDate = newVal ? new Date(newVal) : null;
  if (internalValue.value?.getTime() !== newDate?.getTime()) {
      internalValue.value = newDate;
  }
});

const handleUpdate = (value: any) => {
  // PrimeVue can emit Date, Date[], null, undefined. We only expect Date or null.
  if (Array.isArray(value)) return; 
  
  if (!value) {
      emit('update:modelValue', null);
      emit('change', null);
      return;
  }
  
  if (props.showTime) {
      // Return ISO string for datetime
      const isoString = value.toISOString();
      emit('update:modelValue', isoString);
      emit('change', isoString);
  } else {
      // Format to YYYY-MM-DD for date-only fields
      const year = value.getFullYear();
      const month = String(value.getMonth() + 1).padStart(2, '0');
      const day = String(value.getDate()).padStart(2, '0');
      const dateString = `${year}-${month}-${day}`;
      
      emit('update:modelValue', dateString);
      emit('change', dateString);
  }
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.date-container {
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

// Ensure the root container doesn't have a background
:deep(.custom-prime-datepicker) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
</style>

<style lang="scss">
@use "../../styles/variables" as v;

// Global overrides for the PrimeVue datepicker panel (which is teleported to body)
.p-datepicker-panel,
.custom-prime-datepicker-panel {
    // Override the primary color (green) with app theme color
    --p-primary-color: #{v.$primary-color};
    --p-primary-contrast-color: v.$white;
    --p-datepicker-date-selected-background: #{v.$primary-color};
    --p-datepicker-date-selected-color: v.$white;
    --p-highlight-background: #{v.$primary-color};
    --p-highlight-color: v.$white;
    --p-datepicker-buttonbar-border-color: transparent;
    
    // Prevent panel from stretching - use auto width
    width: auto !important;
    min-width: 260px !important;
    max-width: 320px !important;
    
    .p-datepicker-day-selected {
        background: v.$primary-color !important;
        color: v.$white !important;
    }
    
    .p-datepicker-today > .p-datepicker-day-selected {
        background: v.$primary-color !important;
    }
    
    .p-datepicker-footer {
        padding: 0 !important;
        border-top: none !important;
    }

    // Style the button bar (Today/Clear buttons)
    .p-datepicker-buttonbar,
    .custom-buttonbar {
        padding: 2px 8px 8px 8px !important;
        margin: 0 !important;
        border-top: none !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
        min-width: 100% !important;
        background: v.$white !important;
        box-sizing: border-box !important;
        
        // Style PrimeVue text buttons
        .p-button {
            padding: 4px 8px !important;
            margin: 0 !important;
            font-size: 0.875rem !important;
            min-width: auto !important;
            height: auto !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            
            &.p-button-text {
                color: v.$primary-color !important;
                font-weight: 500 !important;
                
                &:hover {
                    background: v.$overlay-light !important;
                }
            }

            // Secondary/Clear button
            &.p-button-secondary {
                color: v.$text-secondary !important;
                &:hover {
                    color: v.$text-primary !important;
                    background: v.$overlay-light !important;
                }
            }
        }
    }
}
</style>
