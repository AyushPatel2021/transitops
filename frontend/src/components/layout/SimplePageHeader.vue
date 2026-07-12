<template>
  <div class="simple-page-header" v-if="!isMobile">
    <div class="header-left">
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
    </div>
    
    <div class="header-right">
      <NotificationBell />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useResponsive } from '../../composables/useResponsive';
import NotificationBell from '../common/NotificationBell.vue';

const props = defineProps<{
  title: string;
  subtitle?: string;
}>();

const { isMobile } = useResponsive();
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.simple-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 1.5rem;
  padding: 0 1.5rem;
  height: 64px;
  background: v.$white;
  width: 100%;
  z-index: 10;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  
  .page-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: v.$text-primary;
    margin: 0;
    line-height: 1.2;
  }
  
  .page-subtitle {
    font-size: 0.875rem;
    color: v.$text-secondary;
    margin: 0;
    margin-top: 2px;
    line-height: 1.2;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
}
</style>