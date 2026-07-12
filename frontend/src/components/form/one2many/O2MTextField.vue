<template>
  <div class="o2m-text-field">
    <textarea
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      @focus="handleFocus"
      @blur="handleBlur"
      class="o2m-textarea"
      :class="{ 'o2m-textarea-error': invalid, 'o2m-textarea-readonly': readonly, 'has-focus': hasFocus }"
      :readonly="readonly"
      :placeholder="fieldMeta?.label || ''"
      rows="2"
    ></textarea>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  modelValue: string | number | null | undefined;
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

.o2m-text-field {
  width: 100%;
  height: 100%;
}

.o2m-textarea {
  width: 100%;
  min-width: 200px;
  padding: 8px 12px;
  border: none;
  border-bottom: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  color: v.$text-primary;
  font-weight: 500;
  outline: none;
  resize: vertical;
  font-family: inherit;
  transition: all 0.2s ease;
  
  &:hover:not(:read-only) {
    border-bottom-color: v.$border-color;
  }
  
  &.has-focus {
    border-bottom-color: v.$primary-color;
    border-bottom-width: 2px;
    padding-bottom: 7px;
    background-color: rgba(v.$primary-color, 0.02);
  }
  
  &.o2m-textarea-error {
    border-bottom: 1px solid v.$danger-color !important;
    color: v.$danger-color !important;
    
    &:hover {
      border-bottom-color: v.$danger-color;
    }
  }
  
  &.o2m-textarea-readonly {
    color: v.$text-secondary;
    cursor: not-allowed;
    
    &:hover {
      border-bottom-color: transparent;
    }
  }
  
  &::placeholder {
    color: v.$text-secondary;
    font-weight: 400;
  }
}
</style>
