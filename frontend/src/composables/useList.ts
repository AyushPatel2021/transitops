import { ref } from 'vue';
import api from '../core/api';

export function useList(modelName: string) {
    const items = ref<any[]>([]);
    const metadata = ref<any>({});
    const loading = ref(false);
    const error = ref<string | null>(null);

    const totalItems = ref(0);
    const groupedResults = ref<any[]>([]);
    const currentGroupBy = ref<string>('');

    const fetchMetadata = async () => {
        loading.value = true;
        try {
            const response = await api.get(`/models/meta/${modelName}/enhanced`);
            // The enhanced endpoint returns { metadata: {...}, domain_fields: {...}, search_config: {...} }
            // We need to include search_config in metadata for AdvancedSearchBar to access it
            metadata.value = {
                ...response.data.metadata,
                search_config: response.data.search_config || {}
            };
        } catch (err: any) {
            error.value = err.message;
        }
    };

    const fetchItems = async (params: { search?: string, searchField?: string, domain?: string, filters?: any[], groupBy?: string, limit?: number, offset?: number } = {}) => {
        loading.value = true;
        try {
            const queryParams = new URLSearchParams();
            if (params.search) queryParams.append('search', params.search);
            if (params.searchField) queryParams.append('search_field', params.searchField);
            if (params.domain) queryParams.append('domain', params.domain);
            if (params.filters && params.filters.length > 0) {
                // Send filter names as JSON array
                queryParams.append('filters', JSON.stringify(params.filters));
            }
            if (params.groupBy) queryParams.append('groupBy', params.groupBy);
            queryParams.append('limit', (params.limit || 80).toString());
            queryParams.append('offset', (params.offset || 0).toString());

            const response = await api.get(`/models/${modelName}?${queryParams.toString()}`);
            
            // Backend now returns { items: [], total: number, grouped_results?: [], group_by?: string }
            if (response.data && response.data.items) {
                items.value = response.data.items;
                totalItems.value = response.data.total;
                
                // Store grouped results if available
                if (response.data.grouped_results && response.data.group_by) {
                    groupedResults.value = response.data.grouped_results;
                    currentGroupBy.value = response.data.group_by;
                } else {
                    groupedResults.value = [];
                    currentGroupBy.value = '';
                }
            } else {
                // Fallback for legacy calls or unexpected structure
                items.value = Array.isArray(response.data) ? response.data : [];
                totalItems.value = items.value.length;
                groupedResults.value = [];
                currentGroupBy.value = '';
            }
        } catch (err: any) {
            error.value = err.message;
        } finally {
            loading.value = false;
        }
    };

    return { items, totalItems, metadata, loading, error, groupedResults, currentGroupBy, fetchMetadata, fetchItems };
}
