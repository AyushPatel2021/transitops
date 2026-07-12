import { ref, reactive } from 'vue';
import api from '../core/api';
import { useNotifications } from './useNotifications';
import { useErrorHandler } from './useErrorHandler';
import { useUserStore } from '../stores/userStore';

/**
 * Check if the updated record is the current user and refresh userStore if needed
 */
async function checkAndRefreshCurrentUser(modelName: string, recordId: number, updatedData: any) {
    // Only check for user model updates
    if (modelName !== 'user') {
        return;
    }
    
    const userStore = useUserStore();
    
    // Check if the updated user is the current logged-in user
    if (userStore.userData && userStore.userData.id === recordId) {
        
        try {
            // Refresh the user data in the store
            await userStore.refreshUserData();
            
        } catch (error) {
            // Silent error handling
        }
    }
}

export function useForm(modelName: string, id?: number) {
    const formData = reactive<any>({});
    const metadata = ref<any>(null);
    const loading = ref(true); // Start with loading true
    const saving = ref(false); // For save operations
    const isEditing = ref(!id);
    const error = ref<string | null>(null);

    const fetchMetadata = async () => {
        loading.value = true;
        
        try {
            const response = await api.get(`/models/meta/${modelName}/enhanced`);
            
            // The enhanced endpoint returns { metadata: {...}, domain_fields: {...} }
            metadata.value = response.data.metadata;
            if (metadata.value.fields) {
                Object.keys(metadata.value.fields).forEach(key => {
                    if (!(key in formData)) {
                        // Set default values from metadata
                        const fieldMeta = metadata.value.fields[key];
                        if (fieldMeta.default !== undefined) {
                            // Special handling for sequence fields:
                            // If it's a readonly field with default "New", only set it for display
                            // but don't include it in the actual form data until save
                            if (fieldMeta.readonly && fieldMeta.default === "New") {
                                // For sequence fields, we'll handle the display in the component
                                // but not set the actual value until save
                                formData[key] = null;
                            } else {
                                formData[key] = fieldMeta.default;
                            }
                        } else {
                            formData[key] = null;
                        }
                    }
                });
            }
        } catch (err: any) {
            error.value = err.message;
        } finally {
            loading.value = false;
        }
    };

    const fetchRecord = async (recordId: number) => {
        loading.value = true;
        
        try {
            const response = await api.get(`/models/${modelName}/${recordId}?include_domain_states=true`);
            
            Object.assign(formData, response.data);
        } catch (err: any) {
            error.value = err.message;
        } finally {
            loading.value = false;
        }
    };

    const save = async (payload?: any) => {
        saving.value = true;
        error.value = null;
        try {
            const dataToSave = { ...(payload || formData) };
            
            // Special handling for sequence fields:
            // If a field is null/empty and has a "New" default, set it to "New" for the backend
            if (metadata.value?.fields) {
                Object.keys(metadata.value.fields).forEach(key => {
                    const fieldMeta = metadata.value.fields[key];
                    if (fieldMeta.readonly && fieldMeta.default === "New" && 
                        (!dataToSave[key] || dataToSave[key] === null)) {
                        dataToSave[key] = "New";
                    }
                });
            }
            
            const currentId = id || formData.id;
            if (currentId) {
                const response = await api.put(`/models/${modelName}/${currentId}`, dataToSave);
                Object.assign(formData, response.data);
                
                // Check if we updated the current user's record
                await checkAndRefreshCurrentUser(modelName, currentId, response.data);
            } else {
                const response = await api.post(`/models/${modelName}`, dataToSave);
                // Clear the form data first, then assign the response
                Object.keys(formData).forEach(key => {
                    delete formData[key];
                });
                Object.assign(formData, response.data);
                
                // Force reactivity update for sequence fields
                if (metadata.value?.fields) {
                    Object.keys(metadata.value.fields).forEach(key => {
                        const fieldMeta = metadata.value.fields[key];
                        if (fieldMeta.readonly && fieldMeta.default === "New" && response.data[key]) {
                            // Ensure the sequence field is properly updated
                            formData[key] = response.data[key];
                        }
                    });
                }
            }
            isEditing.value = false;
        } catch (err: any) {
            const msg = err.response?.data?.detail || err.message || 'An error occurred';
            error.value = msg;
            
            const { handleApiError } = useErrorHandler();
            handleApiError(err, () => save()); // Retry callback
        } finally {
            saving.value = false;
        }
    };

    const fetchDefaults = async () => {
        if (!metadata.value || !metadata.value.fields) return {};
        
        try {
            const fieldsList = Object.keys(metadata.value.fields);
            const response = await api.post(`/models/${modelName}/default_get`, {
                fields: fieldsList
            });
            return response.data || {};
        } catch (err) {
            console.error("Error fetching defaults:", err);
            return {};
        }
    };

    const reset = async () => {
        // First reset to static defaults/nulls
        Object.keys(formData).forEach(key => {
            const fieldMeta = metadata.value?.fields?.[key];
            if (fieldMeta?.default !== undefined) {
                formData[key] = fieldMeta.default;
            } else {
                formData[key] = null;
            }
        });

        // Then fetch and apply dynamic defaults
        const dynamicDefaults = await fetchDefaults();
        Object.assign(formData, dynamicDefaults);
        
        error.value = null;
    };

    const deleteRecord = async (recordId: number) => {
        loading.value = true;
        try {
            await api.delete(`/models/${modelName}/${recordId}`);
        } catch (err: any) {
            error.value = err.message;
            throw err;
        } finally {
            loading.value = false;
        }
    };

    return { formData, metadata, loading, saving, isEditing, error, fetchMetadata, fetchRecord, save, reset, deleteRecord };
}
