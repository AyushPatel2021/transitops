<template>
  <div class="o2m-field-wrapper">
    <SelectionField
      :model-value="modelValue"
      :options="normalizedOptions"
      :readonly="readonly"
      :invalid="invalid"
      :placeholder="fieldMeta?.label || 'Select...'"
      @update:model-value="$emit('update:modelValue', $event)"
      @focus="$emit('focus')"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import SelectionField from '../SelectionField.vue';

const props = defineProps<{
  modelValue: any;
  fieldMeta: any;
  readonly?: boolean;
  invalid?: boolean;
  options?: any; 
}>();

defineEmits(['update:modelValue', 'focus']);

const normalizedOptions = computed(() => {
  // If props.options is provided (from One2manyField resolving generic options)
  if (props.options && props.options.length) {
      if (Array.isArray(props.options[0])) {
          return props.options.map((o: any) => ({ val: o[0], label: o[1] }));
      }
      return props.options;
  }
  
  // Fallback to fieldMeta.options
  const metaOpts = props.fieldMeta?.options;
  
  if (Array.isArray(metaOpts)) {
     // Check if it's [['a','B'], ...] or [{val:'a', label:'B'}]
     if (Array.isArray(metaOpts[0])) {
         return metaOpts.map((o: any) => ({ val: o[0], label: o[1] }));
     }
     // Already in {val, label} or similar object format?
     // Or just list of strings?
     if (typeof metaOpts[0] === 'string') {
        return metaOpts.map(o => ({ val: o, label: o }));
     }
     return metaOpts;
  }
  
  // If dict
  if (metaOpts && typeof metaOpts === 'object') {
     return Object.entries(metaOpts).map(([k, v]) => {
         const label = (v && typeof v === 'object' && 'label' in v) ? (v as any).label : v;
         return { val: k, label: label as string };
     });
  }
  
  return [];
});
</script>

<style scoped>
.o2m-field-wrapper {
  width: 100%;
  padding: 0 12px;
  position: relative;
}

/* Override dropdown width to prevent narrow dropdowns */
:deep(.dropdown-list) {
  min-width: 200px !important;
  width: max-content !important;
  max-width: 300px !important;
}
</style>
