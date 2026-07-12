<template>
  <div class="password-field">
    <div class="password-input-wrapper">
      <input
        :value="modelValue"
        @input="handleInput"
        :type="showPassword ? 'text' : 'password'"
        class="password-input"
        :class="{ 'field-invalid': invalid, 'field-readonly': readonly }"
        :placeholder="placeholder"
        :readonly="readonly"
        :disabled="readonly"
      />
      <button
        v-if="!readonly"
        type="button"
        class="password-toggle"
        @click="showPassword = !showPassword"
        :title="showPassword ? 'Hide password' : 'Show password'"
      >
        <Eye v-if="!showPassword" class="icon-sm" />
        <EyeOff v-else class="icon-sm" />
      </button>
    </div>
    
    <!-- Password requirements (only show when typing and not readonly) -->
    <div v-if="!readonly && modelValue && showRequirements" class="password-requirements">
      <div class="requirement" :class="{ 'valid': hasMinLength }">
        <span class="requirement-icon">{{ hasMinLength ? '✓' : '✗' }}</span>
        At least 8 characters
      </div>
      <div class="requirement" :class="{ 'valid': hasLetter }">
        <span class="requirement-icon">{{ hasLetter ? '✓' : '✗' }}</span>
        At least one letter
      </div>
      <div class="requirement" :class="{ 'valid': hasNumber }">
        <span class="requirement-icon">{{ hasNumber ? '✓' : '✗' }}</span>
        At least one number
      </div>
    </div>
    
    <!-- Validation error -->
    <div v-if="invalid && modelValue && !isPasswordValid" class="validation-error">
      Password does not meet requirements
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { Eye, EyeOff } from 'lucide-vue-next';

const props = defineProps<{
  modelValue: string | null | undefined;
  placeholder?: string;
  readonly?: boolean;
  invalid?: boolean;
  showRequirements?: boolean;
}>();

const emit = defineEmits(['update:modelValue']);

const showPassword = ref(false);

// Password validation
const hasMinLength = computed(() => (props.modelValue || '').length >= 8);
const hasLetter = computed(() => /[A-Za-z]/.test(props.modelValue || ''));
const hasNumber = computed(() => /\d/.test(props.modelValue || ''));

const isPasswordValid = computed(() => 
  hasMinLength.value && hasLetter.value && hasNumber.value
);

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  emit('update:modelValue', target.value);
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.password-field {
  width: 100%;
}

.password-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input {
  width: 100%;
  border: none;
  background: transparent;
  outline: none;
  font-size: 1rem;
  color: v.$text-primary;
  font-weight: 500;
  border-bottom: 1px solid transparent;
  transition: all 0.2s;
  border-radius: 0;
  font-family: inherit;
  height: 32px;
  padding-right: 2.5rem; // Space for toggle button
  
  &:hover {
    border-bottom-color: v.$border-color;
  }

  &:focus {
    border-bottom-color: v.$primary-color !important;
    border-bottom-width: 2px;
    margin-bottom: -1px;
  }
  
  &::placeholder {
    color: v.$text-placeholder;
  }
}

.password-toggle {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  color: v.$text-secondary;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  
  &:hover {
    color: v.$text-primary;
    background: rgba(v.$text-secondary, 0.1);
  }
}

.password-requirements {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: v.$bg-main;
  border: 1px solid v.$border-light;
  border-radius: 6px;
  
  .requirement {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: v.$text-secondary;
    margin-bottom: 0.25rem;
    
    &.valid {
      color: v.$green-500;
      
      .requirement-icon {
        color: v.$green-500;
        font-weight: bold;
      }
    }
    
    &:not(.valid) {
      .requirement-icon {
        color: v.$red-500;
        font-weight: bold;
      }
    }
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .requirement-icon {
    font-size: 0.75rem;
    width: 12px;
    text-align: center;
  }
}

.validation-error {
  color: v.$danger-color;
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

// Field validation styles
.field-invalid {
  border-bottom-color: v.$danger-color !important;
  color: v.$danger-color !important;
  
  &:hover {
    border-bottom-color: v.$danger-color !important;
  }
  
  &:focus {
    border-bottom-color: v.$danger-color !important;
  }
}

.field-readonly {
  background-color: v.$bg-main !important;
  color: v.$text-secondary !important;
  cursor: not-allowed !important;
  
  &:hover {
    border-bottom-color: transparent !important;
  }
  
  &:focus {
    border-bottom-color: transparent !important;
    border-bottom-width: 1px !important;
    margin-bottom: 0 !important;
  }
}

.icon-sm {
  width: 16px;
  height: 16px;
}
</style>