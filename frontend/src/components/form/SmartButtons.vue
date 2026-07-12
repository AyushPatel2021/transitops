<template>
  <div class="smart-buttons" v-if="buttons && buttons.length">
    <div 
      v-for="btn in buttons" 
      :key="btn.name" 
      class="smart-button"
      @click="$emit('action', btn)"
    >
      <div class="btn-icon">
        <component :is="getIcon(btn.icon)" class="icon-md" />
      </div>
      <div class="btn-content">
        <span class="btn-value">{{ getValue(btn.field) }}</span>
        <span class="btn-label">{{ btn.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as Icons from 'lucide-vue-next';

const props = withDefaults(defineProps<{
  buttons?: any[];
  data: any;
}>(), {
  buttons: () => []
});

defineEmits(['action']);

const getIcon = (iconName: string) => {
  return (Icons as any)[iconName] || Icons.HelpCircle;
};

const getValue = (field: string) => {
  // Support nested fields (e.g. 'partner_id.name')
  // logic...
  
  // Simple field access
  const val = props.data[field];
  
  if (val === null || val === undefined) return '0';
  
  if (Array.isArray(val)) {
    return val.length;
  }
  
  if (typeof val === 'object') {
    return val.display_name || val.name || val.id || '0';
  }
  return val;
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.smart-buttons {
  display: flex;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: v.$radius-btn;
  overflow: hidden;
}

// Dark mode smart buttons
[data-theme="dark"] .smart-buttons {
  background: #161b22;
  border-color: #30363d;
}

.smart-button {
  display: flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  min-width: 100px;
  cursor: pointer;
  transition: all 0.2s;
  border-right: 1px solid v.$border-light;
  
  &:first-child {
    border-top-left-radius: v.$radius-btn;
    border-bottom-left-radius: v.$radius-btn;
  }
  
  &:last-child {
    border-right: none;
    border-top-right-radius: v.$radius-btn;
    border-bottom-right-radius: v.$radius-btn;
  }
  
  &:hover {
    background: v.$bg-main;
    
    .btn-icon {
        color: v.$primary-color;
    }
  }
}

// Dark mode smart button
[data-theme="dark"] .smart-button {
  border-right-color: #30363d;
  
  &:hover {
    background: #0d1117;
    
    .btn-icon {
      color: #58a6ff;
    }
  }
}

.btn-icon {
  margin-right: 0.5rem;
  color: v.$text-tertiary;
  display: flex;
  align-items: center;
  transition: color 0.2s;
  
  .icon-md {
    width: 18px;
    height: 18px;
  }
}

// Dark mode button icon
[data-theme="dark"] .btn-icon {
  color: #7d8590;
}

.btn-content {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.btn-label {
  font-size: 0.75rem;
  color: v.$text-secondary;
  font-weight: 500;
}

.btn-value {
  font-size: 0.875rem;
  font-weight: 700;
  color: v.$text-primary;
}

// Dark mode button content
[data-theme="dark"] {
  .btn-label {
    color: #7d8590;
  }
  
  .btn-value {
    color: #e6edf3;
  }
}
</style>
