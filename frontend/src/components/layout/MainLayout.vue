<template>
  <div class="main-layout" :class="{ 'sidebar-collapsed': effectiveCollapsed }">
    <!-- Mobile Top Bar -->
    <div class="mobile-top-bar" v-if="isMobile">
      <button class="mobile-hamburger" @click="isMobileMenuOpen = !isMobileMenuOpen">
        <Menu v-if="!isMobileMenuOpen" />
        <X v-else />
      </button>
      <div class="mobile-logo">
        <div class="logo-container">
          <img :src="logoIcon" alt="TransitOps" class="mobile-logo-img" />
        </div>
        <span class="brand-name">TransitOps</span>
      </div>
      <div class="mobile-header-actions">
        <NotificationBell />
        <div class="mobile-profile-btn" @click="showProfileDropdown = !showProfileDropdown">
          <div class="header-avatar">
            <img v-if="hasValidImage" :src="userImage" alt="Profile" class="avatar-image" />
            <span v-else class="avatar-text">{{ getInitials(userName) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile Overlay -->
    <Transition name="fade">
      <div v-if="isMobile && isMobileMenuOpen" class="mobile-overlay" @click="isMobileMenuOpen = false"></div>
    </Transition>

    <!-- Sidebar -->
    <aside class="sidebar" :class="{ 'mobile-open': isMobileMenuOpen }">
      <div class="sidebar-header" data-id="clean-header">
        <div class="logo-container">
          <img :src="logoIcon" alt="TransitOps" class="sidebar-logo-icon" />
        </div>
        <span v-if="!effectiveCollapsed" class="brand-name">TransitOps</span>
      </div>

      <nav class="sidebar-nav dark-scrollbar">
        <div v-for="group in menuGroups" :key="group.title" class="nav-group">
          <h3 v-if="!effectiveCollapsed">{{ group.title }}</h3>
          <ul>
            <li v-for="item in group.items" :key="item.name" :class="{ 'has-children': item.children }">
              <!-- Single Item -->
              <router-link 
                v-if="!item.children"
                :to="item.path" 
                :class="{ active: isActivePath(item.path) }"
                @click="handleSidebarClick(item.path)"
              >
                <component :is="item.icon" class="icon" />
                <span v-if="!effectiveCollapsed">{{ item.label }}</span>
              </router-link>

              <!-- Parent Item -->
              <div v-else class="nav-parent">
                <div 
                  class="parent-item" 
                  @click="toggleExpand(item.name)"
                  @mouseenter="onParentMouseEnter(item, $event)"
                  @mouseleave="onParentMouseLeave"
                  :class="{ 
                    'expanded': expandedItems.includes(item.name),
                    'active': item.children && item.children.some((child: MenuItem) => isActivePath(child.path))
                  }"
                >
                  <component :is="item.icon" class="icon" />
                  <span v-if="!effectiveCollapsed" class="label">{{ item.label }}</span>
                  <ChevronRight v-if="!effectiveCollapsed" class="chevron" />
                </div>
                
                <!-- Children -->
                <Transition name="slide-down">
                <div class="children-container" v-show="expandedItems.includes(item.name) && !effectiveCollapsed">
                  <div class="tree-line"></div>
                  <router-link 
                    v-for="child in item.children" 
                    :key="child.name"
                    :to="child.path"
                    class="child-item"
                    :class="{ active: isActivePath(child.path) }"
                    @click="handleSidebarClick(child.path)"
                  >
                    <span class="child-label">{{ child.label }}</span>
                  </router-link>
                </div>
                </Transition>
              </div>
            </li>
          </ul>
        </div>
      </nav>
      
      <div class="sidebar-footer">
        <div class="footer-top">
             <!-- On mobile, this button closes the drawer. On desktop, it collapses/expands. -->
             <button class="collapse-btn-footer" @click="isMobile ? isMobileMenuOpen = false : isCollapsed = !isCollapsed" :title="isMobile ? 'Close' : (effectiveCollapsed ? 'Expand' : 'Collapse')">
               <X v-if="isMobile" class="footer-icon-sm" />
               <i v-else :class="effectiveCollapsed ? 'icofont-bubble-right' : 'icofont-bubble-left'"></i>
             </button>
        </div>
      </div>
    </aside>

    <!-- Main Content Container (Header + Content) -->
    <div class="main-content">
      <!-- Fixed Top Header (Desktop) -->
      <header class="top-header" v-if="!isMobile">
        <div class="header-left">
          <Breadcrumbs 
            :items="displayBreadcrumbs" 
            @click="handleBreadcrumbClick"
          />
        </div>
        <div class="header-right">
          <!-- Search Box (Placeholder) -->
          <div class="search-box">
            <Search class="search-icon" />
            <input type="text" placeholder="Search..." disabled />
          </div>
          
          <!-- Notification Bell Wrapper for Button consistency -->
          <div class="header-icon-btn">
            <NotificationBell />
          </div>
          
          <!-- Profile Dropdown -->
          <div class="profile-menu" ref="profileMenuRef">
            <div class="user-menu" @click="showProfileDropdown = !showProfileDropdown">
              <div class="header-avatar shadow-sm">
                <img v-if="hasValidImage" :src="userImage" alt="Profile" class="avatar-image" />
                <span v-else class="avatar-text">{{ getInitials(userName) }}</span>
              </div>
              <div class="user-info" v-if="!effectiveCollapsed">
                <span class="user-name">{{ userName || 'User' }}</span>
                <span class="user-role">{{ userRole }}</span>
              </div>
              <ChevronDown class="chevron-icon" />
            </div>
            
            <!-- Dropdown Menu -->
            <Transition name="pop">
              <div v-if="showProfileDropdown" class="profile-dropdown">
                <router-link to="/profile" class="dropdown-item" @click="showProfileDropdown = false">
                  <User class="dropdown-icon" />
                  View Profile
                </router-link>
                <div class="dropdown-divider"></div>
                <button class="dropdown-item logout" @click="handleLogout">
                  <LogOut class="dropdown-icon" />
                  Sign Out
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </header>

      <!-- Main Content -->
      <main class="content-area" :class="{ 'has-top-header': !isMobile }">
        <div class="page-content">
          <router-view :key="$route.fullPath" />
        </div>
      </main>
    </div>

    <!-- Floating Menu Portal -->
    <Teleport to="body">
      <div 
        v-if="!isMobile && effectiveCollapsed && activeHoverItem && hoveredMenuData"
        class="floating-sidebar-menu"
        :style="{ top: hoverMenuPosition.top + 'px', left: hoverMenuPosition.left + 'px' }"
        @mouseenter="onMenuMouseEnter"
        @mouseleave="onMenuMouseLeave"
      >
        <div class="menu-header">{{ hoveredMenuData.label }}</div>
        <router-link
          v-for="child in hoveredMenuData.children"
          :key="child.name"
          :to="child.path"
          class="floating-item"
          :class="{ active: isActivePath(child.path) }"
          @click="handleSidebarClick(child.path)"
        >
          {{ child.label }}
        </router-link>
      </div>
    </Teleport>
    
    <!-- Profile Dropdown for Mobile (Teleported) -->
    <Teleport to="body">
      <Transition name="pop">
        <div v-if="isMobile && showProfileDropdown" class="mobile-profile-dropdown" ref="mobileProfileRef">
          <div class="dropdown-header">
            <div class="header-avatar large">
              <img v-if="hasValidImage" :src="userImage" alt="Profile" class="avatar-image" />
              <span v-else class="avatar-text">{{ getInitials(userName) }}</span>
            </div>
            <div class="user-details">
              <span class="user-name">{{ userName || 'User' }}</span>
              <span class="user-role">{{ userRole }}</span>
            </div>
          </div>
          <div class="dropdown-divider"></div>
          <router-link to="/profile" class="dropdown-item" @click="showProfileDropdown = false">
            <User class="dropdown-icon" />
            View Profile
          </router-link>
          <div class="dropdown-divider"></div>
          <button class="dropdown-item logout" @click="handleLogout">
            <LogOut class="dropdown-icon" />
            Sign Out
          </button>
        </div>
      </Transition>
      <div v-if="isMobile && showProfileDropdown" class="profile-overlay" @click="showProfileDropdown = false"></div>
    </Teleport>
    
    <NotificationContainer />
    
    <!-- Enhanced Error Dialog -->
    <ErrorDialog
      v-if="errorDialogState.error"
      :show="errorDialogState.show"
      :error="errorDialogState.error"
      :retryable="errorDialogState.retryable"
      @close="closeErrorDialog"
      @retry="retryAction"
      @report="reportError"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { 
  Menu,
  X,
  ChevronLeft, 
  ChevronRight, 
  LayoutDashboard, 
  MonitorSmartphone, 
  BusFront,
  Users, 
  User,
  UserCog,
  UserRoundCheck,
  ShieldCheck, 
  Building2, 
  MapPinned,
  LayoutGrid, 
  LogOut,
  ClipboardList,
  Route,
  Navigation,
  Box,
  ChevronDown,
  Clock,
  Search,
  Database,
  Settings,
  BarChart3,
  Wrench,
  Fuel,
  ReceiptText,
  Gauge,
  Activity,
  TrendingUp,
  BadgeDollarSign
} from 'lucide-vue-next';
import NotificationContainer from '../common/NotificationContainer.vue';
import NotificationBell from '../common/NotificationBell.vue';
import Breadcrumbs from '../common/Breadcrumbs.vue';
import ErrorDialog from '../common/ErrorDialog.vue';
import { useUserStore } from '../../stores/userStore';
import { useBreadcrumbs } from '../../composables/useBreadcrumbs';
import { useErrorHandler } from '../../composables/useErrorHandler';
import api from '../../core/api';
import logoIcon from '../../assets/transitops_mark.svg';


/**
 * MainLayout Component - Secure User Data Management
 * 
 * This component has been updated to use the secure UserStore instead of localStorage
 * for user data access. Key security improvements:
 * 
 * 1. User data is accessed from memory-based UserStore, not localStorage
 * 2. Reactive updates ensure UI reflects user data changes immediately
 * 3. Proper cleanup of subscriptions to prevent memory leaks
 * 4. Authentication state watching for automatic logout handling
 * 5. User data initialization on component mount if needed
 * 
 * Requirements addressed: 6.4, 7.6
 */

interface MenuItem {
  name: string;
  label: string;
  path: string;
  icon: any;
  children?: MenuItem[];
  sequence?: number;
}

interface MenuGroup {
  title: string;
  items: MenuItem[];
}

// Icon mapping for dynamic menu
const iconMap: Record<string, any> = {
  LayoutDashboard,
  MonitorSmartphone,
  BusFront,
  Users,
  UserCog,
  UserRoundCheck,
  ShieldCheck,
  Building2,
  MapPinned,
  LayoutGrid,
  ClipboardList,
  Route,
  Navigation,
  Box,
  Clock,
  Database,
  Settings,
  BarChart3,
  Wrench,
  Fuel,
  ReceiptText,
  Gauge,
  Activity,
  TrendingUp,
  BadgeDollarSign
};

const { requestReset, trail, trimToIndex } = useBreadcrumbs();
const { errorDialogState, closeErrorDialog, retryAction, reportError } = useErrorHandler();

const isMobile = ref(false);
const isMobileMenuOpen = ref(false);
const showProfileDropdown = ref(false);
const profileMenuRef = ref<HTMLElement | null>(null);
const mobileProfileRef = ref<HTMLElement | null>(null);

const isActivePath = (path: string) => {
  const currentRoute = router?.currentRoute?.value;
  const targetRoute = router.resolve(path);
  const currentPath = currentRoute?.path || '';
  const targetPath = targetRoute.path || path;
  const targetHasQuery = Object.keys(targetRoute.query || {}).length > 0;
  const currentIsReportView = currentRoute?.query?.report !== undefined;

  if (targetHasQuery) {
    return currentRoute?.fullPath === targetRoute.fullPath;
  }

  if (targetPath.startsWith('/models/')) {
    return !currentIsReportView && (
      currentPath === targetPath || currentPath.startsWith(`${targetPath}/`)
    );
  }

  if (targetPath === '/') return currentPath === '/';
  return currentPath === targetPath || currentPath.startsWith(`${targetPath}/`);
};

// Computed breadcrumbs that shows page name when trail is empty (non-model screens)
const displayBreadcrumbs = computed(() => {
  if (trail.value.length > 0) {
    return trail.value;
  }
  
  // For non-model screens, get the current page name from sidebar menu or route meta
  const currentPath = router?.currentRoute?.value?.path || '/';
  const routeMeta = router?.currentRoute?.value?.meta;
  
  // Check if route has a meta title (e.g., Profile page)
  if (routeMeta?.title) {
    return [{ label: routeMeta.title as string, path: currentPath }];
  }
  
  // Find matching menu item
  for (const group of menuGroups.value) {
    for (const item of group.items) {
      // Check direct match
      if (item.path === currentPath) {
        return [{ label: item.label, path: item.path }];
      }
      // Check children
      if (item.children) {
        for (const child of item.children) {
          if (currentPath === child.path || currentPath.startsWith(`${child.path}/`)) {
            return [{ label: child.label, path: child.path }];
          }
        }
      }
    }
  }
  
  // Default fallback - capitalize the path segment
  const pathParts = currentPath.split('/').filter(Boolean);
  if (pathParts.length > 0) {
    const label = pathParts[0].charAt(0).toUpperCase() + pathParts[0].slice(1).replace(/-/g, ' ');
    return [{ label, path: currentPath }];
  }
  
  return [];
});

const updateIsMobile = () => {
    isMobile.value = window.innerWidth < 1024;
    if (!isMobile.value) isMobileMenuOpen.value = false;
};

const menuGroups = ref<MenuGroup[]>([]);

const fetchMenu = async () => {
    try {
        const resp = await api.get('/models/ui/menu');
        // Map string icons to components
        menuGroups.value = resp.data.map((group: any) => ({
            ...group,
            items: group.items.map((item: any) => ({
                ...item,
                icon: iconMap[item.icon] || LayoutGrid,
                children: item.children ? item.children.map((child: any) => ({
                    ...child,
                    icon: iconMap[child.icon] || LayoutGrid
                })) : undefined
            }))
        }));
    } catch (e) {
        // Failed to fetch menu - handle silently
    }
};

onMounted(async () => {
    updateIsMobile();
    window.addEventListener('resize', updateIsMobile);
    fetchMenu();
    
    // Subscribe to user store updates for reactive UI updates
    const unsubscribeUserUpdates = userStore.onUserDataUpdate((eventType, userData) => {
      // The computed properties will automatically update the UI
      // when userData changes in the store
      if (eventType === 'login_completed' || eventType === 'logout_completed' || 
          eventType === 'preferences_updated' || eventType === 'manual_refresh' ||
          eventType === 'token_refreshed' || eventType === 'preferences_synced' ||
          eventType === 'data_refreshed' || eventType === 'startup_completed' ||
          eventType === 'initialization_completed') {
        // Force reactivity update for avatar and user info
        // The computed properties should handle this automatically, but we can
        // trigger a small update to ensure UI consistency
        if (eventType === 'logout_completed') {
          // Ensure UI is cleared on logout
        }
      }
    });
    
    // Store unsubscribe function for cleanup
    (window as any).__mainLayoutUnsubscribe = unsubscribeUserUpdates;
    
    // Click outside handler for profile dropdown
    const handleClickOutside = (e: MouseEvent) => {
      if (profileMenuRef.value && !profileMenuRef.value.contains(e.target as Node)) {
        showProfileDropdown.value = false;
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    (window as any).__profileClickOutside = handleClickOutside;
});

onUnmounted(() => {
    window.removeEventListener('resize', updateIsMobile);
    
    // Cleanup user store subscription
    if ((window as any).__mainLayoutUnsubscribe) {
      (window as any).__mainLayoutUnsubscribe();
      delete (window as any).__mainLayoutUnsubscribe;
    }
    
    // Cleanup profile click outside handler
    if ((window as any).__profileClickOutside) {
      document.removeEventListener('mousedown', (window as any).__profileClickOutside);
      delete (window as any).__profileClickOutside;
    }
});

const handleSidebarClick = (path: string) => {
    activeHoverItem.value = null; 
    if (isMobile.value) isMobileMenuOpen.value = false;
    
    // Explicitly clear trail on sidebar click to ensure we don't show stale breadcrumbs
    trail.value = [];
    requestReset();
    
    // If it's the same path, we want to force GenericView to re-init
    // We can do this by setting a global 'lastInit' timestamp or similar, 
    // but the easiest way is to let GenericView watch the trail length.
    // I'll add that watch to GenericView.
};

// Handle breadcrumb navigation from top header
const handleBreadcrumbClick = (bc: any, idx: number) => {
    
    trimToIndex(idx);
    router.push({
        path: bc.path,
        query: bc.query || {}
    });
    showProfileDropdown.value = false;
};

// Initialize from local storage for persistence
const isCollapsed = ref(localStorage.getItem('sidebar_collapsed') === 'true');
const effectiveCollapsed = computed(() => isMobile.value ? false : isCollapsed.value);
const savedExpandedItems = localStorage.getItem('sidebar_expanded_items');
const expandedItems = ref<string[]>(savedExpandedItems ? JSON.parse(savedExpandedItems) : []);

// Watch for changes and save to local storage
watch(isCollapsed, (val) => {
  localStorage.setItem('sidebar_collapsed', val.toString());
});

watch(expandedItems, (val) => {
  localStorage.setItem('sidebar_expanded_items', JSON.stringify(val));
}, { deep: true });

const userStore = useUserStore();
const router = useRouter();

// Watch for authentication state changes
watch(() => userStore.isAuthenticated, (isAuth) => {
  if (!isAuth && router.currentRoute.value.path !== '/login') {
    
    router.push('/login');
  }
}, { immediate: true });

// Watch for user data loading to ensure sidebar shows correct info
watch(() => userStore.userData, (userData) => {
  if (userData) {
    
  }
}, { immediate: true });

// Computed properties for reactive user data from UserStore
const user = computed(() => userStore.userData);
const userImage = computed(() => userStore.userImage);
const userName = computed(() => userStore.userName || 'Loading...');
const userRole = computed(() => {
  if (userStore.isLoading) return 'Loading...';
  return userStore.userData?.role?.label || userStore.userData?.role?.name || 'Member';
});

// Computed property to check if user has a valid image
const hasValidImage = computed(() => {
  return !!(userImage.value && 
         userImage.value !== null && 
         userImage.value !== '' && 
         userImage.value !== 'null' && 
         userImage.value !== 'undefined');
});

const handleLogout = async () => {
  try {
    await userStore.logoutReactive();
    router.push('/login');
  } catch (error) {
    // Force navigation to login even if logout fails
    router.push('/login');
  }
};

const toggleExpand = (name: string) => {
    if (expandedItems.value.includes(name)) {
        expandedItems.value = expandedItems.value.filter((i: string) => i !== name);
    } else {
        expandedItems.value.push(name);
    }
};

// Floating Menu Logic
const activeHoverItem = ref<string | null>(null);
const hoverMenuPosition = ref({ top: 0, left: 0 });
let hoverTimeout: any = null;

const hoveredMenuData = computed(() => {
  if (!activeHoverItem.value) return null;
  for (const group of menuGroups.value) {
    const found = group.items.find((i: MenuItem) => i.name === activeHoverItem.value);
    if (found) return found;
  }
  return null;
});

const onParentMouseEnter = (item: any, event: MouseEvent) => {
  if (!isCollapsed.value || !item.children) return;
  
  if (hoverTimeout) clearTimeout(hoverTimeout);
  
  const target = (event.currentTarget as HTMLElement);
  const rect = target.getBoundingClientRect();
  
  hoverMenuPosition.value = {
    top: rect.top,
    left: rect.right + 12 // small gap
  };
  activeHoverItem.value = item.name;
};

const onParentMouseLeave = () => {
  hoverTimeout = setTimeout(() => {
    activeHoverItem.value = null;
  }, 100); // 100ms delay to allow moving to popup
};

const onMenuMouseEnter = () => {
  if (hoverTimeout) clearTimeout(hoverTimeout);
};

const onMenuMouseLeave = () => {
  onParentMouseLeave();
};

// Helper function to get user initials
const getInitials = (name: string) => {
  if (!name) return 'U';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.main-layout {
  display: flex;
  height: 100vh;
  background: v.$bg-main;
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
}

.mobile-top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: v.$white;
  border-bottom: 1px solid v.$border-color;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  z-index: 1001;
  box-shadow: 0 2px 4px v.$black-transparent-05;

  .mobile-logo {
    margin-left: 1rem;
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.75rem;

    .logo-container {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;

      .mobile-logo-img {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }
    }

    .brand-name {
      font-size: 1.125rem;
      font-weight: 700;
      color: v.$text-primary;
      letter-spacing: -0.02em;
    }
  }

  .mobile-header-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
}

.mobile-hamburger {
  background: v.$bg-main;
  border: 1px solid v.$border-color;
  width: 40px;
  height: 40px;
  border-radius: v.$radius-btn;
  display: flex;
  align-items: center;
  justify-content: center;
  color: v.$text-primary;
  cursor: pointer;
  
  &:hover { background: v.$border-light; }
}

.mobile-overlay {
  position: fixed;
  inset: 0;
  background: v.$overlay-modal;
  backdrop-filter: blur(2px);
  z-index: 999;
}

.sidebar {
  width: 280px;
  height: 100vh;
  background: v.$bg-sidebar;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 1000;

  @media (max-width: 1023px) {
    position: fixed;
    left: -280px;
    &.mobile-open {
      left: 0;
    }
  }

  .sidebar-header {
    height: 64px;
    display: flex;
    align-items: center;
    padding: 0 20px;
    gap: 12px;
    flex-shrink: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    
    .logo-container {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      
      .sidebar-logo-icon {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }
    }

    .brand-name {
      font-size: 18px;
      font-weight: 700;
      color: v.$white;
      white-space: nowrap;
      transition: opacity 0.2s;
    }
  }

  .sidebar-nav {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 16px 12px;
    
    .nav-group {
      margin-bottom: 24px;
      
      h3 {
        padding: 0 12px;
        font-size: 11px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
      }
      
      ul { 
        list-style: none; 
        padding: 0; 
        margin: 0; 
      }
      
      // Top Level Items
      a, .parent-item {
        display: flex;
        align-items: center;
        padding: 10px 12px;
        color: rgba(255, 255, 255, 0.6);
        text-decoration: none;
        border-radius: v.$radius-md;
        margin-bottom: 2px;
        transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        gap: 12px;
        
        .icon { 
          width: 20px; 
          height: 20px; 
          min-width: 20px;
          flex-shrink: 0;
        }
        
        span { 
          font-size: 14px; 
          font-weight: 500;
          white-space: nowrap;
          flex: 1;
        }
        
        &:hover { 
          background: rgba(255, 255, 255, 0.08);
          color: v.$white;
        }
        
        &.active { 
          background: rgba(37, 99, 235, 0.15);
          color: v.$primary-color;
        }
      }

      .parent-item {
        justify-content: space-between;
        
        .chevron { 
          width: 16px; 
          height: 16px; 
          margin-left: auto; 
          transition: transform 0.2s;
          color: rgba(255, 255, 255, 0.4);
        }
        
        &.expanded .chevron { 
          transform: rotate(90deg); 
          color: v.$white;
        }
        
        &.active {
          background: rgba(37, 99, 235, 0.15);
          color: v.$primary-color;
          
          .chevron {
            color: v.$primary-color;
          }
        }
        
        &:hover .chevron { 
          color: v.$white; 
        }
        
        .icon { margin-right: 0; }
        .label { margin-left: 0; margin-right: auto; }
      }
      
      // Child Container
      .children-container {
        position: relative;
        padding-left: 32px;
        margin-top: 4px;

        .tree-line {
          display: none;
        }

        .child-item {
          position: relative;
          padding: 8px 12px;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 2px;
          border-radius: v.$radius-md;
          margin-left: 0;
          transition: all 0.15s;

          &::before {
            content: '';
            position: absolute;
            left: -20px;
            top: 0;
            width: 12px;
            height: 50%;
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            border-bottom-left-radius: 6px;
          }
          
          &:not(:last-child)::after {
            content: '';
            position: absolute;
            left: -20px;
            top: 50%;
            bottom: -2px;
            width: 1px;
            background-color: rgba(255, 255, 255, 0.1);
          }
          
          &:hover { 
            background: rgba(255, 255, 255, 0.08);
            color: v.$white;
          }
          
          &.active {
            background: rgba(37, 99, 235, 0.15);
            color: v.$primary-color;
            font-weight: 600;
          }
        }
      }
    }
  }

  .sidebar-footer {
    padding: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    background: v.$bg-sidebar;
    flex-shrink: 0;

    .footer-top {
      display: flex;
      justify-content: center;
    }

    .collapse-btn-footer {
      width: 100%;
      height: 40px;
      padding: 0;
      background: transparent;
      border: none;
      color: rgba(255, 255, 255, 0.6);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.15s;
      border-radius: v.$radius-md;
      font-size: 14px;
      font-weight: 500;
      
      &:hover {
        color: v.$primary-color;
        background: rgba(255, 255, 255, 0.08);
      }
      
      i, .footer-icon-sm {
        font-size: 24px;
        line-height: 1;
      }
    }

    .user-block {
      display: flex;
      align-items: center;
      
      .user-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        padding: 10px 12px;
        border-radius: v.$radius-md;
        transition: background 0.15s;
        
        &:hover {
          background: rgba(255, 255, 255, 0.08);
        }
      }
      
      .collapsed-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        width: 100%;
      }
      
      .user-info-full {
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;
        text-decoration: none;
        color: inherit;
        flex: 1;
        
        .avatar {
          width: 36px; 
          height: 36px; 
          background: linear-gradient(135deg, v.$primary-color, #3b82f6);
          border-radius: 50%; 
          display: flex; 
          align-items: center; 
          justify-content: center;
          font-weight: 600; 
          color: v.$white;
          overflow: hidden;
          flex-shrink: 0;
          font-size: 14px;
          
          .avatar-image {
            width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 10px;
                }
                
                .avatar-text {
                    color: v.$white;
                    font-weight: 600;
                    font-size: 1rem;
                }
            }
            .details {
                min-width: 0;
                .name { 
                    font-size: 0.9rem; 
                    font-weight: 600; 
                    color: v.$white; 
                    margin: 0 0 2px 0;
                }
                .role { 
                    font-size: 0.75rem; 
                    color: v.$text-secondary; 
                    margin: 0;
                }
            }
        }
        
        // Collapsed Avatar Only
        .avatar.collapsed {
             width: 40px; 
             height: 40px; 
             background: v.$primary-color;
             border-radius: 10px; 
             display: flex; 
             align-items: center; 
             justify-content: center;
             font-weight: 600; 
             color: v.$white; 
             text-decoration: none;
             transition: all 0.2s;
             overflow: hidden;
             
             &:hover {
                 transform: scale(1.05);
                 box-shadow: 0 4px 12px v.$shadow-dark;
             }
             
             .avatar-image {
                 width: 100%;
                 height: 100%;
                 object-fit: cover;
                 border-radius: 10px;
             }
             
             .avatar-text {
                 color: v.$white !important;
                 font-weight: 600 !important;
                 font-size: 1rem !important;
                 display: block !important;
                 visibility: visible !important;
                 opacity: 1 !important;
             }
        }

        .logout-btn {
            background: transparent; 
            border: none; 
            color: v.$text-secondary;
            cursor: pointer; 
            padding: 0.5rem; 
            transition: all 0.2s;
            border-radius: v.$radius-btn;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            
            .icon {
                width: 18px;
                height: 18px;
            }
            
            &:hover { 
                color: v.$red-500;
                transform: scale(1.1);
            }
            
            &.collapsed {
                width: 40px;
                height: 40px;
                
                .icon {
                    width: 20px;
                    height: 20px;
                }
                
                &:hover {
                    color: v.$red-500;
                    transform: scale(1.05);
                }
            }
        }
    }
  }
}

.sidebar-collapsed {
  .sidebar {
    width: 70px;
    
    .sidebar-header { 
      justify-content: center; 
      padding: 0; 
      
      .brand-name {
        opacity: 0;
        display: none;
      }
    }
    
    .nav-group {
      h3 { display: none; }
      
      // Hide text and chevron in collapsed state
      a, .parent-item {
        justify-content: center;
        padding: 10px;
        
        span, .label, .chevron { 
          opacity: 0;
          display: none; 
        }
        
        .icon { margin: 0; }
      }
      
      // Hide children when collapsed
      .children-container { 
        display: none !important; 
      }
    }

    .sidebar-footer {
      padding: 12px 8px;
      
      .collapse-btn-footer {
        height: 40px;
        padding: 0;
        
        i {
          font-size: 24px;
        }
      }
      
      .user-block {
        .collapsed-container {
          gap: 1rem;
        }
      }
    }
  }
}

.collapse-btn-footer {
  background: transparent; 
  border: none; 
  color: rgba(255, 255, 255, 0.6);
  border-radius: v.$radius-md; 
  height: 40px;
  padding: 0;
  cursor: pointer; 
  display: flex; 
  align-items: center; 
  justify-content: center;
  width: 100%;
  transition: all 0.15s;
  gap: 8px;
  
  &:hover { 
    color: v.$primary-color; 
    background: rgba(255, 255, 255, 0.08); 
  }

  i, .footer-icon-sm {
    font-size: 24px;
    line-height: 1;
  }
}

// ========== DARK MODE SPECIFIC STYLES ==========
[data-theme="dark"] {
  .sidebar {
    background: #161b22;
    border-right: 1px solid #30363d;
    
    .sidebar-header {
      border-bottom: 1px solid #30363d;
    }
    
    .sidebar-nav {
      .nav-group {
        h3 {
          display: block;
          color: #7d8590;
        }
        
        a, .parent-item {
          color: #7d8590;
          
          &:hover {
            background: #1c2128;
            color: #e6edf3;
          }
          
          &.active {
            background: rgba(37, 99, 235, 0.1);
            color: #2563eb;
          }
        }
        
        .parent-item {
          .chevron {
            color: #7d8590;
          }
          
          &.expanded .chevron {
            color: #e6edf3;
          }
          
          &.active .chevron {
            color: #2563eb;
          }
          
          &:hover .chevron {
            color: #e6edf3;
          }
        }
        
        .children-container {
          .child-item {
            color: #7d8590;
            
            &::before {
              border-left-color: #30363d;
              border-bottom-color: #30363d;
            }
            
            &:not(:last-child)::after {
              background-color: #30363d;
            }
            
            &:hover {
              background: #1c2128;
              color: #e6edf3;
            }
            
            &.active {
              background: rgba(37, 99, 235, 0.1);
              color: #2563eb;
            }
          }
        }
      }
    }
    
    .sidebar-footer {
      border-top: 1px solid #30363d;
      background: #161b22;
      
      .collapse-btn-footer {
        color: #7d8590;
        
        &:hover {
          color: #2563eb;
          background: #1c2128;
        }
      }
      
      .user-block {
        .user-container:hover {
          background: #1c2128;
        }
        
        .user-info-full {
          .details {
            .name {
              color: #e6edf3;
            }
            .role {
              color: #7d8590;
            }
          }
        }
      }
    }
  }
}
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  min-width: 0;

  @media (max-width: 1023px) {
    width: 100vw;
    padding-top: 56px; // Space for mobile top bar
  }
  
  &.has-top-header {
    padding-top: 0; // Content is positioned after header in flow
  }
}

// Main content container (header + content area)
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  min-height: 0;
  min-width: 0;
  
  @media (max-width: 1023px) {
    width: 100vw;
    padding-top: 56px; // Space for mobile top bar
  }
}

.page-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  min-height: 0;
  min-width: 0;
  width: 100%;
}

// ========== FIXED TOP HEADER ==========
.top-header {
  height: 64px;
  background: v.$white;
  border-bottom: 1px solid v.$border-color;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  gap: 1.25rem;
  flex-shrink: 0;
  z-index: 50;
}

// Dark mode header styles
[data-theme="dark"] .top-header {
  background: #161b22;
  border-bottom: 1px solid #30363d;
}

.header-left {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  transition: all 0.2s;
  
  &:hover {
    background: v.$bg-main;
  }
}

// Dark mode header icon button
[data-theme="dark"] .header-icon-btn {
  &:hover {
    background: #1c2128;
  }
}

// Search Box
.search-box {
  position: relative;
  width: 280px;
  
  input {
    width: 100%;
    padding: 8px 36px 8px 36px;
    background: v.$bg-main;
    border: 1px solid v.$border-color;
    border-radius: 12px;
    color: v.$text-primary;
    font-size: 14px;
    transition: all 0.2s;
    
    &:focus {
      outline: none;
      border-color: v.$primary-color;
      background: v.$white;
      box-shadow: 0 0 0 3px rgba(v.$primary-color, 0.1);
    }
    
    &:disabled {
      cursor: not-allowed;
      opacity: 0.7;
    }
    
    &::placeholder {
      color: v.$text-placeholder;
    }
  }
  
  .search-icon {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: v.$text-secondary;
    pointer-events: none;
    width: 18px;
    height: 18px;
  }
}

// Dark mode search box
[data-theme="dark"] .search-box {
  input {
    background: #0d1117;
    border-color: #30363d;
    color: #e6edf3;
    
    &:focus {
      background: #161b22;
      border-color: #2563eb;
    }
    
    &::placeholder {
      color: #7d8590;
    }
  }
  
  .search-icon {
    color: #7d8590;
  }
}

// Profile Menu
.profile-menu {
  position: relative;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px 6px 6px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
  
  &:hover {
    background: v.$bg-main;
  }

  .chevron-icon {
    width: 16px;
    height: 16px;
    color: v.$text-secondary;
    margin-left: 2px;
  }
}

// Dark mode user menu
[data-theme="dark"] .user-menu {
  &:hover {
    background: #1c2128;
  }
  
  .chevron-icon {
    color: #7d8590;
  }
}

.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;

  .user-name {
    font-size: 13px;
    font-weight: 600;
    color: v.$text-primary;
  }

  .user-role {
    font-size: 11px;
    color: v.$text-secondary;
  }
}

// Dark mode user info
[data-theme="dark"] .user-info {
  .user-name {
    color: #e6edf3;
  }
  
  .user-role {
    color: #7d8590;
  }
}

.header-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: v.$white;
  font-weight: 600;
  font-size: 12px;
  overflow: hidden;
  flex-shrink: 0;
  background: transparent;
  
  &.large {
    width: 48px;
    height: 48px;
    font-size: 1rem;
  }
  
  .avatar-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .avatar-text {
    color: v.$white;
    font-weight: 600;
    background: linear-gradient(135deg, v.$primary-color, #6366f1);
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
  }
}

.user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  
  .user-name {
    font-size: 0.8125rem;
    font-weight: 600;
    color: v.$text-primary;
    line-height: 1.2;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
  }
  
  .user-role {
    font-size: 0.6875rem;
    color: v.$text-secondary;
    line-height: 1.2;
  }
}

.chevron-icon {
  width: 16px;
  height: 16px;
  color: v.$text-secondary;
  transition: transform 0.2s;
}

// Profile Dropdown
.profile-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 12px;
  box-shadow: 0 10px 25px -5px v.$shadow-color-md;
  min-width: 200px;
  z-index: 100;
  overflow: hidden;
}

[data-theme="dark"] .profile-dropdown {
  background: #161b22;
  border: 1px solid #30363d;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: v.$text-primary;
  text-decoration: none;
  font-size: 0.875rem;
  transition: all 0.15s;
  background: none;
  border: none;
  width: 100%;
  cursor: pointer;
  
  &:hover {
    background: v.$bg-main;
    color: v.$primary-color;
  }
  
  &.logout {
    color: v.$red-500;
    
    &:hover {
      background: rgba(v.$red-500, 0.08);
      color: v.$red-600;
    }
  }
}

[data-theme="dark"] .dropdown-item {
  color: #e6edf3;
  
  &:hover {
    background: #0d1117;
    color: #58a6ff;
  }
  
  &.logout {
    color: #f85149;
    
    &:hover {
      background: rgba(248, 81, 73, 0.1);
      color: #ff7b72;
    }
  }
}

.dropdown-icon {
  width: 18px;
  height: 18px;
}

.dropdown-divider {
  height: 1px;
  background: v.$border-color;
}

[data-theme="dark"] .dropdown-divider {
  background: #30363d;
}

// Mobile Profile Button
.mobile-profile-btn {
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 50%;
  transition: background 0.2s;
  
  &:hover {
    background: v.$bg-main;
  }
}

[data-theme="dark"] .mobile-profile-btn {
  &:hover {
    background: #1c2128;
  }
}

// Mobile Profile Dropdown
.mobile-profile-dropdown {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: v.$white;
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -10px 30px -5px v.$shadow-color-md;
  z-index: 2000;
  padding: 1.5rem;
  
  .dropdown-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .user-details {
    display: flex;
    flex-direction: column;
    
    .user-name {
      font-size: 1rem;
      font-weight: 600;
      color: v.$text-primary;
    }
    
    .user-role {
      font-size: 0.75rem;
      color: v.$text-secondary;
    }
  }
}

[data-theme="dark"] .mobile-profile-dropdown {
  background: #161b22;
  box-shadow: 0 -10px 30px -5px rgba(0, 0, 0, 0.5);
  
  .user-details {
    .user-name {
      color: #e6edf3;
    }
    
    .user-role {
      color: #7d8590;
    }
  }
}

.profile-overlay {
  position: fixed;
  inset: 0;
  background: v.$overlay-modal;
  z-index: 1999;
}

// Child Menu Slide Transition
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}

.slide-down-enter-to,
.slide-down-leave-from {
  opacity: 1;
  max-height: 400px; // Increased for mobile
  transform: translateY(0);
}

// Pop Transition for dropdowns
.pop-enter-active, .pop-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}

.pop-enter-from, .pop-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

<style lang="scss">
// Global styles for teleported menu
@use "../../styles/variables" as v;

.floating-sidebar-menu {
  position: fixed;
  z-index: 9999;
  background: #1e1e2d; // Dark theme bg
  border: 1px solid v.$white-transparent-10;
  border-radius: 6px;
  box-shadow: 0 4px 12px v.$overlay-modal;
  padding: 0.5rem 0;
  min-width: 200px;
  
  .menu-header {
    padding: 0.5rem 1rem;
    font-weight: 600;
    color: v.$white;
    border-bottom: 1px solid v.$white-transparent-10;
    margin-bottom: 0.5rem;
    background: v.$white-transparent-05;
  }

  .floating-item {
    display: block;
    padding: 0.5rem 1rem;
    color: #a2a5b9;
    text-decoration: none;
    font-size: 0.9rem;
    transition: all 0.2s;
    
    &:hover {
      background: v.$white-transparent-10;
      color: v.$white;
      text-decoration: none;
    }
    
    &.active {
      color: v.$primary-color;
      background: rgba(v.$primary-color, 0.1);
    }
  }
}
</style>
