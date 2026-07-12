<template>
  <div class="o2m-field-wrapper">
    <DateTimeField
      :model-value="modelValue"
      :readonly="readonly"
      :invalid="invalid"
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import DateTimeField from '../DateTimeField.vue';

defineProps<{
  modelValue: any;
  readonly?: boolean;
  invalid?: boolean;
  fieldMeta?: any;
}>();

defineEmits(['update:modelValue']);
</script>

<style scoped>
.o2m-field-wrapper {
  width: 100%;
  padding: 0 12px;
  position: relative;
}

/* Hide the date picker icon in table context */
:deep(.p-datepicker-input-icon-container) {
  display: none !important;
}

/* Remove extra padding since no icon */
:deep(.custom-prime-input),
:deep(.p-datepicker-input) {
  padding-right: 0 !important;
}

/* Make the entire input clickable for date picker */
:deep(.custom-prime-datepicker) {
  cursor: pointer;
}

:deep(.p-datepicker-input) {
  cursor: pointer;
}

/* Ensure readonly state shows proper cursor */
:deep(.is-readonly .p-datepicker-input) {
  cursor: not-allowed !important;
}
</style>
