import { ref, computed, onMounted, onUnmounted } from 'vue';

export interface ResponsiveConfig {
  breakpoints: {
    mobile: number;
    tablet: number;
    desktop: number;
  };
}

const defaultConfig: ResponsiveConfig = {
  breakpoints: {
    mobile: 768,
    tablet: 1024,
    desktop: 1200
  }
};

export function useResponsive(config: ResponsiveConfig = defaultConfig) {
  const screenWidth = ref(0);
  
  const updateScreenWidth = () => {
    screenWidth.value = window.innerWidth;
  };

  const isMobile = computed(() => screenWidth.value < config.breakpoints.mobile);
  const isTablet = computed(() => 
    screenWidth.value >= config.breakpoints.mobile && 
    screenWidth.value < config.breakpoints.desktop
  );
  const isDesktop = computed(() => screenWidth.value >= config.breakpoints.desktop);
  
  const screenSize = computed(() => {
    if (isMobile.value) return 'mobile';
    if (isTablet.value) return 'tablet';
    return 'desktop';
  });

  // Touch device detection
  const isTouchDevice = computed(() => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  });

  // Responsive grid columns for forms
  const formColumns = computed(() => {
    if (isMobile.value) return 1;
    if (isTablet.value) return 1;
    return 2;
  });

  // Return all columns requested (mobile now supports horizontal scrolling)
  const getEssentialColumns = (allColumns: string[], metadata: any) => {
    return allColumns;
  };

  // Touch-friendly minimum sizes
  const touchTargetSize = computed(() => ({
    minHeight: isTouchDevice.value ? '44px' : '36px',
    minWidth: isTouchDevice.value ? '44px' : '36px'
  }));

  onMounted(() => {
    updateScreenWidth();
    window.addEventListener('resize', updateScreenWidth);
  });

  onUnmounted(() => {
    window.removeEventListener('resize', updateScreenWidth);
  });

  return {
    screenWidth,
    isMobile,
    isTablet,
    isDesktop,
    screenSize,
    isTouchDevice,
    formColumns,
    getEssentialColumns,
    touchTargetSize,
    breakpoints: config.breakpoints
  };
}