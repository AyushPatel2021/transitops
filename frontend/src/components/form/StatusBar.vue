<template>
  <div class="znova-status-bar">
    <div class="status-stages">
      <div 
        v-for="(stage, index) in reversedStages" 
        :key="stage.val"
        class="stage-item"
        :class="{ 
          'active': currentValue === stage.val,
          'clickable': !readonly 
        }"
        @click="handleStageClick(stage.val)"
      >
        <span class="stage-label">{{ stage.label }}</span>
        <div class="chevron" v-if="index < reversedStages.length - 1"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  stages: { label: string; val: any }[];
  currentValue: any;
  readonly?: boolean;
}>();

const emit = defineEmits(['change']);

const handleStageClick = (val: any) => {
  if (props.readonly) return;
  emit('change', val);
};

// Znova status bars usually show stages from right to left in terms of progression 
// but we render them in the order provided. We reverse the display if needed 
// or just handle the chevron logic.
const reversedStages = computed(() => [...props.stages].reverse());
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.znova-status-bar {
  display: flex;
  align-items: center;
  height: 100%;
}

.status-stages {
  display: flex;
  flex-direction: row-reverse; // Standard Znova layout: active stage on the right-ish
  align-items: stretch;
  height: 32px;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 10px;
  overflow: hidden;
}

// Dark mode status stages
[data-theme="dark"] .status-stages {
  background: #161b22;
  border-color: #30363d;
}

.stage-item {
  position: relative;
  display: flex;
  align-items: center;
  padding: 0 1.25rem 0 1.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: v.$text-secondary;
  &.clickable {
    cursor: pointer;
  }

  &:not(.clickable) {
    cursor: default;
  }

  &:last-child {
    padding-left: 1.25rem;
  }

  &.active {
    background: v.$primary-color;
    color: v.$white;
    
    &::after {
      border-left-color: v.$primary-color;
    }
  }

  &:not(.active):hover {
    background: v.$bg-main;
    color: v.$text-primary;
    
    &::after {
      border-left-color: v.$bg-main;
    }
  }

  // The Arrow / Chevron tip
  &::after {
    content: "";
    position: absolute;
    right: -10px;
    top: 0;
    width: 0;
    height: 0;
    border-top: 16px solid transparent;
    border-bottom: 16px solid transparent;
    border-left: 10px solid v.$white;
    z-index: 2;
    transition: border-color 0.2s ease;
  }

  // The Arrow / Chevron notch on the left
  &::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 0;
    height: 0;
    border-top: 16px solid transparent;
    border-bottom: 16px solid transparent;
    border-left: 10px solid v.$border-color;
    z-index: 1;
  }
  
  &:first-child::after {
    display: none; // End of the bar
  }
  
  &:last-child::before {
    display: none; // Start of the bar
  }
}

// Dark mode stage item
[data-theme="dark"] .stage-item {
  color: #7d8590;
  
  &.active {
    background: #2563eb;
    color: white;
    
    &::after {
      border-left-color: #2563eb;
    }
  }
  
  &:not(.active):hover {
    background: #0d1117;
    color: #e6edf3;
    
    &::after {
      border-left-color: #0d1117;
    }
  }
  
  &::after {
    border-left-color: #161b22;
  }
  
  &::before {
    border-left-color: #30363d;
  }
}

.stage-label {
  position: relative;
  z-index: 3;
}
</style>
