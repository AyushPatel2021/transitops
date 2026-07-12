<template>
  <div class="o2m-float-field">
    <input 
      v-if="!readonly"
      type="number"
      step="0.01"
      :value="modelValue"
      @input="handleInput"
      @focus="handleFocus"
      @blur="handleBlur"
      class="o2m-input"
      :class="{ 'has-focus': hasFocus, 'o2m-input-error': invalid }"
      :placeholder="fieldMeta?.placeholder || ''"
    />
    <div v-else class="o2m-field-readonly">
      {{ formatFloat(modelValue) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  modelValue: number | string | null | undefined;
  fieldMeta: any;
  readonly: boolean;
  invalid?: boolean;
}>();

const emit = defineEmits(['update:modelValue', 'focus']);

const hasFocus = ref(false);

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target) return;
  const value = target.value;
  if (!value) {
    emit('update:modelValue', null);
  } else {
    const parsed = parseFloat(value);
    emit('update:modelValue', isNaN(parsed) ? null : parsed);
  }
};

const handleFocus = () => {
  hasFocus.value = true;
  emit('focus');
};

const handleBlur = () => {
  hasFocus.value = false;
};

const formatFloat = (value: any) => {
  if (value === null || value === undefined) return '-';
  const num = parseFloat(value);
  if (isNaN(num)) return '-';
  return num.toFixed(2);
};
</script>

<style lang="scss" scoped>
@use "../../../styles/variables" as v;

.o2m-float-field {
  width: 100%;
  height: 100%;
}

.o2m-input {
  width: 100%;
  height: 100%;
  text-align: right;
  padding: 8px 12px;
  border: none;
  border-bottom: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  color: v.$text-primary;
  font-weight: 500;
  outline: none;
  transition: all 0.2s ease;
  
  &:hover {
    border-bottom-color: v.$border-color;
  }
  
  &.has-focus {
    border-bottom-color: v.$primary-color;
    border-bottom-width: 2px;
    padding-bottom: 7px;
    background-color: rgba(v.$primary-color, 0.02);
  }
  
  &.o2m-input-error {
    border-bottom: 1px solid v.$danger-color !important;
    color: v.$danger-color !important;
    
    &:hover {
      border-bottom-color: v.$danger-color;
    }
  }
  
  &::placeholder {
    color: v.$text-secondary;
    font-weight: 400;
  }
}

.o2m-field-readonly {
  text-align: right;
  padding: 8px 12px;
  color: v.$text-secondary;
}
</style>
