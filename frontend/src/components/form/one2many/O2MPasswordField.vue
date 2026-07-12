<template>
  <div class="o2m-password-field">
    <input
      v-if="!readonly"
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @focus="handleFocus"
      @blur="handleBlur"
      type="password"
      class="o2m-input"
      :class="{ 'o2m-input-error': invalid, 'has-focus': hasFocus }"
      :placeholder="fieldMeta?.label || 'Password'"
    />
    <div v-else class="o2m-field-readonly">
      {{ modelValue ? '••••••••' : '-' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  modelValue: string | null | undefined;
  fieldMeta: any;
  readonly: boolean;
  invalid?: boolean;
}>();

const emit = defineEmits(['update:modelValue', 'focus']);

const hasFocus = ref(false);

const handleFocus = () => {
  hasFocus.value = true;
  emit('focus');
};

const handleBlur = () => {
  hasFocus.value = false;
};
</script>

<style lang="scss" scoped>
@use "../../../styles/variables" as v;

.o2m-password-field {
  width: 100%;
  height: 100%;
}

.o2m-input {
  width: 100%;
  min-width: 120px;
  padding: 8px 12px;
  border: none;
  border-bottom: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  color: v.$text-primary;
  font-weight: 500;
  outline: none;
  transition: all 0.2s ease;
  height: 100%;
  
  &:hover {
    border-bottom-color: v.$border-color;
  }
  
  &.has-focus {
    border-bottom-color: v.$primary-color;
    border-bottom-width: 2px;
    padding-bottom: 7px;
    background: rgba(v.$primary-color, 0.02);
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
  padding: 8px 12px;
  color: v.$text-secondary;
}
</style>
