import { ref } from 'vue';
import api from '../core/api';

/**
 * Composable for managing relational field data (one2many and many2many)
 * Provides caching and domain filtering support
 */
export function useRelationalFields(modelName: string) {
  const relatedRecords = ref<Map<string, any[]>>(new Map());
  const availableOptionsCache = ref<Map<string, any[]>>(new Map());
  const loading = ref(false);
  const error = ref<string | null>(null);

  /**
   * Fetch related records for a one2many or many2many field
   * Results are cached to avoid redundant API calls
   * 
   * @param fieldName - Name of the relational field
   * @param recordIds - Array of record IDs to fetch
   * @param comodelName - Name of the related model (optional, uses modelName if not provided)
   * @returns Array of related records
   */
  async function fetchRelatedRecords(
    fieldName: string,
    recordIds: number[],
    comodelName?: string
  ): Promise<any[]> {
    if (!recordIds || recordIds.length === 0) {
      return [];
    }

    // Check cache first
    const cacheKey = `${fieldName}-${recordIds.sort().join(',')}`;
    if (relatedRecords.value.has(cacheKey)) {
      return relatedRecords.value.get(cacheKey)!;
    }

    loading.value = true;
    error.value = null;

    try {
      const targetModel = comodelName || modelName;
      const filters = [['id', 'in', recordIds]];
      
      const response = await api.get(`/models/${targetModel}`, {
        params: {
          filters: JSON.stringify(filters)
        }
      });

      const records = response.data.items || [];
      
      // Cache the results
      relatedRecords.value.set(cacheKey, records);
      
      return records;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch related records';
      error.value = errorMessage;
      return [];
    } finally {
      loading.value = false;
    }
  }

  /**
   * Fetch available options for many2many dropdown
   * Supports excluding already-selected items and domain filtering
   * Results are cached based on the combination of parameters
   * 
   * @param comodelName - Name of the related model
   * @param excludeIds - Array of IDs to exclude from results (already selected)
   * @param domain - Domain filter expression (JSON string or array)
   * @returns Array of available option records
   */
  async function fetchAvailableOptions(
    comodelName: string,
    excludeIds: number[] = [],
    domain: string | any[] | null = null
  ): Promise<any[]> {
    // Create cache key based on all parameters
    const sortedExcludeIds = [...excludeIds].sort();
    const domainStr = domain ? (typeof domain === 'string' ? domain : JSON.stringify(domain)) : '';
    const cacheKey = `${comodelName}-exclude:${sortedExcludeIds.join(',')}-domain:${domainStr}`;

    // Check cache first
    if (availableOptionsCache.value.has(cacheKey)) {
      return availableOptionsCache.value.get(cacheKey)!;
    }

    loading.value = true;
    error.value = null;

    try {
      const filters: any[] = [];

      // Add exclusion filter
      if (excludeIds.length > 0) {
        filters.push(['id', 'not in', excludeIds]);
      }

      // Add domain filter
      if (domain) {
        let domainFilters: any[];
        
        if (typeof domain === 'string') {
          try {
            domainFilters = JSON.parse(domain);
          } catch (e) {
            domainFilters = [];
          }
        } else {
          domainFilters = domain;
        }

        if (Array.isArray(domainFilters) && domainFilters.length > 0) {
          filters.push(...domainFilters);
        }
      }

      const response = await api.get(`/models/${comodelName}`, {
        params: {
          filters: filters.length > 0 ? JSON.stringify(filters) : undefined
        }
      });

      const options = response.data.items || [];
      
      // Cache the results
      availableOptionsCache.value.set(cacheKey, options);
      
      return options;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch available options';
      error.value = errorMessage;
      return [];
    } finally {
      loading.value = false;
    }
  }

  /**
   * Clear all cached data
   * Useful when data needs to be refreshed
   */
  function clearCache() {
    relatedRecords.value.clear();
    availableOptionsCache.value.clear();
  }

  /**
   * Clear cache for a specific field or model
   * 
   * @param key - Cache key pattern to match (partial match)
   */
  function clearCacheFor(key: string) {
    // Clear related records cache
    const relatedKeys = Array.from(relatedRecords.value.keys()).filter(k => k.includes(key));
    relatedKeys.forEach(k => relatedRecords.value.delete(k));

    // Clear available options cache
    const optionKeys = Array.from(availableOptionsCache.value.keys()).filter(k => k.includes(key));
    optionKeys.forEach(k => availableOptionsCache.value.delete(k));
  }

  return {
    relatedRecords,
    availableOptionsCache,
    loading,
    error,
    fetchRelatedRecords,
    fetchAvailableOptions,
    clearCache,
    clearCacheFor
  };
}
