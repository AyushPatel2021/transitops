import { ref, watch } from 'vue';

export interface BreadcrumbItem {
  label: string;
  path: string;
  query?: any;
  view?: 'list' | 'form';
  id?: string | number;
  domain?: any;
  context?: any;
}

const STORAGE_KEY = 'gg_breadcrumb_trail';

// Global state shared across all instances of the composable
const trail = ref<BreadcrumbItem[]>([]);

// Initialize from session storage
const saved = sessionStorage.getItem(STORAGE_KEY);
if (saved) {
  try {
    trail.value = JSON.parse(saved);
  } catch (e) {
    // Silently handle breadcrumb parsing errors
  }
}

// Persist to session storage whenever it changes
watch(trail, (newTrail) => {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(newTrail));
}, { deep: true });

// Flag to signal that the next GenericView init should reset the trail (e.g. sidebar click)
const needsReset = ref(false);

const normalizeQuery = (query: any): string => {
  if (!query) return '{}';
  if (typeof query === 'string') return query;
  // Sort keys for consistent comparison
  const sorted = Object.keys(query).sort().reduce((acc, key) => {
    acc[key] = query[key];
    return acc;
  }, {} as any);
  return JSON.stringify(sorted);
};

const normalizeDomain = (domain: any): string => {
  if (!domain) return '[]';
  if (Array.isArray(domain)) return JSON.stringify(domain);
  if (typeof domain === 'string') {
    try {
      return JSON.stringify(JSON.parse(domain));
    } catch {
      return domain;
    }
  }
  return JSON.stringify(domain);
};

export function useBreadcrumbs() {
  const push = (item: BreadcrumbItem) => {
    
    const itemDomainStr = normalizeDomain(item.domain);
    
    const existingIndex = trail.value.findIndex(t => {
        
        // For Form views, we match primarily on path and ID
        if (item.view === 'form' && t.view === 'form') {
            const match = t.path === item.path && t.id === item.id;
            return match;
        }
        
        // For List views, we match on path and normalized domain ONLY
        // Query parameters (filters, search, groupBy) should NOT create new breadcrumbs
        // They should update the existing breadcrumb
        const tDomainStr = normalizeDomain(t.domain);
        const pathMatch = t.path === item.path;
        const domainMatch = tDomainStr === itemDomainStr;
        
        
        return pathMatch && domainMatch;
    });
    
    
    if (existingIndex !== -1) {
      // Znova behavior: If navigating back to an existing point in history, 
      // prune everything after it.
      trail.value = trail.value.slice(0, existingIndex + 1);
      // Update with latest metadata (label, query might have changed etc)
      trail.value[existingIndex] = { ...trail.value[existingIndex], ...item };
    } else {
      trail.value.push(item);
    }
    
  };

  const setTrail = (items: BreadcrumbItem[]) => {
    trail.value = items;
  };

  const pop = () => {
    trail.value.pop();
  };

  const reset = (rootItem?: BreadcrumbItem) => {
    trail.value = rootItem ? [rootItem] : [];
  };

  const requestReset = () => {
    needsReset.value = true;
  };

  const consumeReset = () => {
    if (needsReset.value) {
      trail.value = [];
      needsReset.value = false;
      return true;
    }
    return false;
  };

  const trimToIndex = (index: number) => {
    if (index >= 0 && index < trail.value.length) {
      trail.value = trail.value.slice(0, index + 1);
    }
  };

  const updateLast = (item: Partial<BreadcrumbItem>) => {
    if (trail.value.length > 0) {
      trail.value[trail.value.length - 1] = {
        ...trail.value[trail.value.length - 1],
        ...item
      };
    }
  };

  const trimToPath = (path: string) => {
    const idx = trail.value.findIndex(t => t.path === path);
    if (idx !== -1) {
      trail.value = trail.value.slice(0, idx + 1);
    }
  };

  return {
    trail,
    push,
    setTrail,
    pop,
    reset,
    requestReset,
    consumeReset,
    trimToIndex,
    updateLast,
    trimToPath
  };
}
