<template>
  <div class="boolean-field" :class="{ 'readonly': readonly }">
    <!-- Toggle Switch Style -->
    <div class="toggle-switch" @click="!readonly && toggle()">
      <input 
        type="checkbox" 
        :checked="modelValue" 
        :disabled="readonly"
        :class="{ 'field-invalid': invalid }"
        @change="handleChange"
        class="toggle-input"
      />
      <span class="toggle-slider" :class="{ 'active': modelValue, 'readonly': readonly }">
        <span class="toggle-knob"></span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean;
  readonly?: boolean;
  invalid?: boolean;
  label?: string;
}>();

const emit = defineEmits(['update:modelValue']);

const handleChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  emit('update:modelValue', target.checked);
};

const toggle = () => {
  emit('update:modelValue', !props.modelValue);
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.boolean-field {
  display: flex;
  align-items: center;
  min-height: 40px;
  
  &.readonly {
    opacity: 0.7;
  }
}

.toggle-switch {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  
  &:hover:not(.readonly) .toggle-slider {
    background-color: rgba(v.$primary-color, 0.1);
  }
}

.toggle-input {
  display: none; // Hide the actual checkbox
}

.toggle-slider {
  position: relative;
  width: 48px;
  height: 24px;
  background-color: v.$gray-200;
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 1px solid v.$gray-300;
  
  &.active {
    background-color: v.$primary-color;
    border-color: v.$primary-color;
  }
  
  &.readonly {
    cursor: not-allowed;
    opacity: 0.6;
  }
  
  // Invalid state
  .toggle-input.field-invalid + & {
    border-color: v.$danger-color;
    box-shadow: 0 0 0 1px v.$danger-color;
  }
}

.toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background-color: v.$white;
  border-radius: 50%;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px v.$shadow-dark;
  
  .toggle-slider.active & {
    transform: translateX(24px);
  }
}

// Alternative checkbox style (commented out, can be used instead)
/*
.checkbox-style {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  
  .checkbox-input {
    width: 18px;
    height: 18px;
    border: 2px solid v.$gray-300;
    border-radius: 4px;
    background: v.$white;
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:checked {
      background-color: v.$primary-color;
      border-color: v.$primary-color;
      
      &::after {
        content: '✓';
        color: v.$white;
        font-size: 12px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
      }
    }
    
    &.field-invalid {
      border-color: v.$danger-color;
    }
  }
  
  .checkbox-label {
    font-size: 14px;
    color: v.$text-primary;
    cursor: pointer;
  }
}
*/
</style>