<template>
  <div class="o2m-field-wrapper">
    <Many2manyField
      :model-value="modelValue || []"
      :metadata="fieldMeta"
      :readonly="readonly"
      :invalid="invalid"
      :context="context"
      @update:model-value="$emit('update:modelValue', $event)"
      @error="$emit('error', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import Many2manyField from '../Many2manyField.vue';

const props = defineProps<{
  modelValue: any;
  fieldMeta: any;
  readonly?: boolean;
  invalid?: boolean;
  context?: Record<string, any>;
}>();

defineEmits(['update:modelValue', 'error', 'focus']);
</script>

<style scoped>
.o2m-field-wrapper {
  width: 100%;
  min-width: 250px;
  padding: 8px 12px;
}

/* Override standard field styles to blend better in table */
:deep(.input-wrapper) {
  border-bottom: 1px solid transparent;
}

:deep(.input-wrapper:hover) {
  border-bottom-color: v.$border-color;
}

/* Ensure pills have proper spacing from table borders */
:deep(.pills-container) {
  margin: 0;
  padding: 0;
}

:deep(.pill) {
  margin: 2px 4px 2px 0;
}
</style>
