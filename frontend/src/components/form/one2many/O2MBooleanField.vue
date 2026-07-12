<template>
  <div class="o2m-boolean-field">
    <div v-if="readonly" class="o2m-field-readonly">
      <span class="o2m-readonly-indicator" :class="{ 'active': modelValue }">
        <span class="o2m-readonly-dot"></span>
      </span>
    </div>
    <div v-else class="o2m-toggle-switch" @click="toggle">
      <input 
        type="checkbox" 
        :checked="modelValue" 
        :class="{ 'o2m-input-error': invalid }"
        @change="handleChange"
        class="o2m-toggle-input"
      />
      <span class="o2m-toggle-slider" :class="{ 'active': modelValue }">
        <span class="o2m-toggle-knob"></span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean;
  fieldMeta: any;
  readonly: boolean;
  invalid?: boolean;
}>();

const emit = defineEmits(['update:modelValue', 'focus']);

const handleChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  emit('update:modelValue', target.checked);
  emit('focus');
};

const toggle = () => {
  emit('update:modelValue', !props.modelValue);
  emit('focus');
};
</script>

<style lang="scss" scoped>
@use "../../../styles/variables" as v;

.o2m-boolean-field {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
}

.o2m-field-readonly {
  color: v.$text-secondary;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.o2m-readonly-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: v.$disabled-bg;
  border: 1px solid v.$table-border;
  
  &.active {
    background-color: v.$primary-color;
    border-color: v.$primary-color;
    
    .o2m-readonly-dot {
      background-color: v.$white;
    }
  }
}

.o2m-readonly-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: v.$disabled-text;
}

.o2m-toggle-switch {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  
  &:hover .o2m-toggle-slider:not(.readonly) {
    background-color: rgba(v.$primary-color, 0.1);
  }
}

.o2m-toggle-input {
  display: none; // Hide the actual checkbox
  
  &.o2m-input-error + .o2m-toggle-slider {
    border-color: v.$danger-color !important;
    box-shadow: 0 0 0 1px v.$danger-color;
  }
}

.o2m-toggle-slider {
  position: relative;
  width: 36px;
  height: 18px;
  background-color: v.$table-border;
  border-radius: 9px;
  transition: all 0.2s ease;
  border: 1px solid v.$table-border;
  flex-shrink: 0;
  
  &.active {
    background-color: v.$primary-color;
    border-color: v.$primary-color;
  }
}

.o2m-toggle-knob {
  position: absolute;
  top: 1px;
  left: 1px;
  width: 14px;
  height: 14px;
  background-color: v.$white;
  border-radius: 50%;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px v.$shadow-dark;
  
  .o2m-toggle-slider.active & {
    transform: translateX(18px);
  }
}
</style>