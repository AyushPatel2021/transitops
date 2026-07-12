import { ref, computed, watch, onMounted, unref, Ref, ComputedRef } from 'vue';
import api from '../core/api';
import { useUserStore } from '../stores/userStore';

interface Permissions {
  create: boolean;
  read: boolean;
  write: boolean;
  delete: boolean;
}

interface ActionPermissions {
  showCreateButton: boolean;
  showSaveButton: boolean;
  showDiscardButton: boolean;
  showDeleteButton: boolean;
  showEditActions: boolean;
  makeFieldsReadonly: boolean;
  allowFormSubmission: boolean;
}

export function useUnifiedPermissions(modelName: string, recordId?: number | string | Ref<number | string> | ComputedRef<number | string>) {
  const userStore = useUserStore();
  
  const permissions = ref<Permissions>({
    create: false,
    read: false,
    write: false,
    delete: false
  });
  
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Basic permission getters
  const canCreate = computed(() => permissions.value.create);
  const canRead = computed(() => permissions.value.read);
  const canWrite = computed(() => permissions.value.write);
  const canDelete = computed(() => permissions.value.delete);

  // Action-level permissions for UI components
  const actionPermissions = computed<ActionPermissions>(() => {
    const id = unref(recordId);
    const isNewRecord = id === 'new';
    const isListView = id === 'list' || id === undefined;
    const isExistingRecord = !isNewRecord && !isListView;
    
    const result = {
      // Create button - only show if user can create (for list view and new records)
      showCreateButton: permissions.value.create,
      
      // Save button - show if user can create (new record) or write (existing record)
      showSaveButton: isNewRecord ? permissions.value.create : (isExistingRecord ? permissions.value.write : false),
      
      // Discard button - show when save button is shown
      showDiscardButton: isNewRecord ? permissions.value.create : (isExistingRecord ? permissions.value.write : false),
      
      // Delete button - show if user can delete AND (it's an existing record OR we are in list view)
      showDeleteButton: permissions.value.delete && (isExistingRecord || isListView),
      
      // Edit actions (header buttons) - only show if user can write on existing records
      showEditActions: permissions.value.write && isExistingRecord,
      
      // Make fields readonly - if user can't write on existing records
      makeFieldsReadonly: isExistingRecord && !permissions.value.write,
      
      // Allow form submission - if user can create (new) or write (existing)
      allowFormSubmission: isNewRecord ? permissions.value.create : (isExistingRecord ? permissions.value.write : false)
    };
    
    return result;
  });

  // Permission-aware CSS classes
  const getPermissionClasses = (element: string) => {
    const classes: string[] = [];
    
    if (element === 'form' && actionPermissions.value.makeFieldsReadonly) {
      classes.push('form-readonly');
    }
    
    if (element === 'create-button' && !actionPermissions.value.showCreateButton) {
      classes.push('hidden');
    }
    
    if (element === 'delete-button' && !actionPermissions.value.showDeleteButton) {
      classes.push('hidden');
    }
    
    return classes.join(' ');
  };

  // Fetch permissions from backend
  const fetchPermissions = async () => {
    if (!modelName) {
      return;
    }
    
    const id = unref(recordId);
    loading.value = true;
    error.value = null;
    
    try {
      let response;
      
      if (id && id !== 'new' && id !== 'list') {
        // Get record-specific permissions
        response = await api.get(`/models/${modelName}/${id}/permissions`);
      } else {
        // Get model-level permissions (for new records, list view, or when no recordId)
        response = await api.get(`/models/${modelName}/permissions`);
      }
      
      permissions.value = response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch permissions';
      
      // Fallback: Check if user is admin and give full permissions
      const isAdmin = userStore.userRole === 'admin';
      
      if (isAdmin) {
        permissions.value = {
          create: true,
          read: true,
          write: true,
          delete: true
        };
      } else {
        // Fallback to no permissions on error for non-admin users
        permissions.value = {
          create: false,
          read: false,
          write: false,
          delete: false
        };
      }
    } finally {
      loading.value = false;
    }
  };

  // Refresh permissions manually
  const refreshPermissions = () => {
    fetchPermissions();
  };

  // Handle permission errors gracefully
  const handlePermissionError = (operation: string) => {
    const messages = {
      create: 'You do not have permission to create new records.',
      read: 'You do not have permission to view this record.',
      write: 'You do not have permission to modify this record.',
      delete: 'You do not have permission to delete this record.'
    };
    
    return messages[operation as keyof typeof messages] || 'Permission denied.';
  };

  // Watch for changes in recordId to refetch permissions
  // Handle both reactive and non-reactive recordId values
  if (typeof recordId === 'object' && recordId !== null) {
    // recordId is reactive (ref or computed)
    watch(recordId, (newId, oldId) => {
      fetchPermissions();
    }, { immediate: false });
  } else {
    // recordId is a static value, no need to watch
    // Permissions will be fetched on mount
  }

  // Initial fetch
  onMounted(() => {
    fetchPermissions();
  });

  return {
    // Basic permissions
    permissions: computed(() => permissions.value),
    canCreate,
    canRead,
    canWrite,
    canDelete,
    
    // Action permissions for UI
    actionPermissions,
    
    // Utility functions
    getPermissionClasses,
    refreshPermissions,
    handlePermissionError,
    
    // State
    loading: computed(() => loading.value),
    error: computed(() => error.value)
  };
}