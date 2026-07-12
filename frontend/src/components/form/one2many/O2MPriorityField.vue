<template>
  <div class="o2m-field-wrapper">
    <PriorityField
      :model-value="modelValue"
      :readonly="readonly"
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import PriorityField from '../PriorityField.vue';

defineProps<{
  modelValue: any;
  readonly?: boolean;
  fieldMeta?: any;
}>();

defineEmits(['update:modelValue']);
</script>

<style scoped>
.o2m-field-wrapper {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
}
</style>
