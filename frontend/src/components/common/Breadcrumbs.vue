<template>
  <div class="breadcrumbs-container">
    <div class="breadcrumbs-trail">
      <!-- Collapsed Menu if trail > 4 -->
      <template v-if="items.length > 4">
        <div class="breadcrumb-more" ref="menuRef">
          <button class="more-btn" @click.stop="toggleMenu" title="Show more">
            <MoreHorizontal class="icon-sm" />
          </button>
          
          <transition name="pop">
            <div v-if="showMenu" class="more-menu">
              <div 
                v-for="(bc, idx) in hiddenItems" 
                :key="idx"
                class="menu-item"
                @click="handleMenuClick(bc, idx)"
              >
                {{ bc.label }}
              </div>
            </div>
          </transition>
        </div>
        <span class="separator"><ChevronRight class="separator-icon" /></span>
      </template>

      <!-- Visible Items (Last 4) -->
      <template v-for="(bc, idx) in visibleItems" :key="idx">
        <span 
          class="breadcrumb-item" 
          :class="{ 
            link: isLink(bc, idx), 
            current: isCurrent(bc, idx) 
          }"
          @click="isLink(bc, idx) ? $emit('click', bc, getRealIndex(idx)) : null"
        >
          {{ bc.label }}
        </span>
        <span v-if="idx < visibleItems.length - 1" class="separator"><ChevronRight class="separator-icon" /></span>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { MoreHorizontal, ChevronRight } from 'lucide-vue-next';

interface BreadcrumbItem {
  label: string;
  path: string;
  query?: any;
  view?: 'list' | 'form';
  id?: string | number;
}

const props = defineProps<{
  items: BreadcrumbItem[];
}>();

const emit = defineEmits(['click']);

const showMenu = ref(false);
const menuRef = ref<HTMLElement | null>(null);

const hiddenItems = computed(() => {
  if (props.items.length <= 4) return [];
  return props.items.slice(0, props.items.length - 4);
});

const visibleItems = computed(() => {
  if (props.items.length <= 4) return props.items;
  return props.items.slice(props.items.length - 4);
});

const isLink = (bc: any, visibleIdx: number) => {
  const realIdx = getRealIndex(visibleIdx);
  return realIdx < props.items.length - 1;
};

const isCurrent = (bc: any, visibleIdx: number) => {
  const realIdx = getRealIndex(visibleIdx);
  return realIdx === props.items.length - 1;
};

const getRealIndex = (visibleIdx: number) => {
  if (props.items.length <= 4) return visibleIdx;
  return props.items.length - 4 + visibleIdx;
};

const toggleMenu = () => {
  showMenu.value = !showMenu.value;
};

const handleMenuClick = (bc: any, idx: number) => {
  emit('click', bc, idx);
  showMenu.value = false;
};

const handleClickOutside = (e: MouseEvent) => {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    showMenu.value = false;
  }
};

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside);
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.breadcrumbs-container {
  display: flex;
  align-items: center;
}

.breadcrumbs-trail {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.breadcrumb-item {
  font-size: 0.875rem; // 14px
  font-weight: 500;
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.15s;

  @media (max-width: 1023px) {
    font-size: 0.8125rem; // 13px
    max-width: 110px;
  }
  
  &.link {
    color: v.$text-secondary;
    cursor: pointer;
    text-transform: capitalize;
    
    &:hover { 
      color: v.$primary-color;
      text-decoration: none; 
    }
  }
  
  &.current {
    color: v.$text-primary;
    font-weight: 600;
  }
}

// Dark mode breadcrumb
[data-theme="dark"] .breadcrumb-item {
  &.link {
    color: #7d8590;
    
    &:hover {
      color: #2563eb;
    }
  }
  
  &.current {
    color: #e6edf3;
  }
}

.separator {
  color: v.$text-placeholder;
  margin: 0 0.25rem;
  display: flex;
  align-items: center;
  
  .separator-icon {
    width: 14px;
    height: 14px;
  }

  @media (max-width: 1023px) {
    .separator-icon {
      width: 12px;
      height: 12px;
    }
  }
}

// Dark mode separator
[data-theme="dark"] .separator {
  color: #7d8590;
}

.breadcrumb-more {
  position: relative;
  display: flex;
  align-items: center;
  
  .more-btn {
    background: v.$bg-main;
    border: none;
    border-radius: 4px;
    padding: 2px 6px;
    cursor: pointer;
    color: v.$text-secondary;
    display: flex;
    align-items: center;
    transition: all 0.2s;
    
    &:hover {
      background: v.$border-light;
      color: v.$primary-color;
    }
  }
}

// Dark mode more button
[data-theme="dark"] .breadcrumb-more {
  .more-btn {
    background: #1c2128;
    color: #7d8590;
    
    &:hover {
      background: #30363d;
      color: #2563eb;
    }
  }
}

.more-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px v.$shadow-color-md;
  min-width: 180px;
  z-index: 100;
  padding: 4px 0;
  overflow: hidden;

  .menu-item {
    padding: 0.6rem 1rem;
    font-size: 0.9rem;
    color: v.$text-primary;
    cursor: pointer;
    transition: all 0.1s;
    text-transform: capitalize;
    
    &:hover {
      background: v.$bg-main;
      color: v.$primary-color;
    }
  }
}

// Dark mode more menu
[data-theme="dark"] .more-menu {
  background: #161b22;
  border-color: #30363d;
  
  .menu-item {
    color: #e6edf3;
    
    &:hover {
      background: #1c2128;
      color: #2563eb;
    }
  }
}

.icon-sm {
  width: 16px;
  height: 16px;
}

/* Transitions */
.pop-enter-active, .pop-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.pop-enter-from, .pop-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}
</style>
