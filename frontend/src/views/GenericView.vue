<template>
  <div class="generic-view">
    <div class="view-content-root" v-if="viewMode">
      <div v-if="viewMode === 'list'">
        <BaseList 
          :title="title" 
          :items="listItems" 
          :totalCount="listTotal"
          :offset="currentOffset"
          :limit="pageSize"
          :metadata="listMetadata"
          :loading="listLoading"
          :error="listError"
          :search="currentSearch"
          :filters="currentFilters"
          :group-by="currentGroupBy"
          :breadcrumbs="breadcrumbs"
          :grouped-results="listGroupedResults"
          :active-group-by="listCurrentGroupBy"
          :model-name="model"
          @view="handleView"
          @create="handleCreate"
          @search="handleSearch"
          @filter="handleFilter"
          @group-by="handleGroupBy"
          @paginate="handlePaginate"
          @refresh="refreshList"
          @breadcrumb-click="(bc, idx) => handleBreadcrumbClick(bc, idx)"
          @bulk-delete="handleBulkDeleteRequest"
        />
      </div>
      <div v-else-if="viewMode === 'form' && (formLoading || formMetadata)" class="detail-container">
        <BaseForm 
          :modelName="model"
          :formData="formData"
          :metadata="formMetadata"
          :loading="formLoading"
          :saving="formSaving"
          :error="formError"
          :currentIndex="currentIndex"
          :totalInPage="listItems.length"
          :breadcrumbs="breadcrumbs"
          @save="handleSave"
          @cancel="handleCancel"
          @create="handleCreate"
          @logout="handleGlobalLogout"
          @nav="handleNav"
          @breadcrumb-click="(bc, idx) => handleBreadcrumbClick(bc, idx)"
          @action="handleAction"
        />
      </div>
    </div>

    <!-- Confirmation Dialog -->
    <ConfirmationDialog 
      :show="confirmState.show"
      :title="confirmState.title"
      :message="confirmState.message"
      :severity="confirmState.severity"
      :loading="confirmState.loading"
      @confirm="confirmState.action"
      @cancel="confirmState.show = false"
    />
    
    <!-- Wizard Dialog -->
    <WizardDialog
      :show="wizardState.show"
      :loading="wizardState.loading"
      :model-name="wizardState.modelName"
      :wizard-id="wizardState.wizardId"
      :metadata="wizardState.metadata"
      :initial-data="wizardState.data"
      @close="closeWizard"
      @action-complete="handleWizardComplete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, reactive } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useList } from '../composables/useList';
import { useForm } from '../composables/useForm';
import BaseList from '../components/list/BaseList.vue';
import BaseForm from '../components/form/BaseForm.vue';
import ConfirmationDialog from '../components/common/ConfirmationDialog.vue';
import api from '../core/api';
import { useNotifications } from '../composables/useNotifications';
import { useErrorHandler } from '../composables/useErrorHandler';
import { useBreadcrumbs } from '../composables/useBreadcrumbs';
import WizardDialog from '../components/common/WizardDialog.vue';
import { useWizard } from '../composables/useWizard';
import { useDialog } from '../composables/useDialog';

// Setup Wizard State
const { wizardState, openWizard, closeWizard } = useWizard();
const { alert, confirm, prompt } = useDialog();

const props = defineProps<{
  model: string;
  title: string;
  initialId?: string;
}>();

const router = useRouter();
const route = useRoute();
const viewMode = ref<'list' | 'form' | null>(null);
const currentIndex = ref(0);

const currentSearch = ref('');
const currentSearchField = ref('');
const currentDomain = ref('');
const currentFilters = ref<any[]>([]);
const currentGroupBy = ref('');
const currentOffset = ref(0);
const pageSize = 80;

const { 
  items: listItems, 
  totalItems: listTotal,
  metadata: listMetadata, 
  loading: listLoading, 
  error: listError,
  groupedResults: listGroupedResults,
  currentGroupBy: listCurrentGroupBy,
  fetchMetadata: fetchListMeta, 
  fetchItems 
} = useList(props.model);

const {
  formData,
  metadata: formMetadata,
  loading: formLoading,
  saving: formSaving,
  error: formError,
  isEditing: formIsEditing,
  fetchMetadata: fetchFormMeta,
  fetchRecord,
  save,
  reset: formReset,
  deleteRecord: deleteFormRecord
} = useForm(props.model);

// Confirmation Dialog State
const confirmState = reactive({
  show: false,
  title: '',
  message: '',
  severity: 'warning' as 'info' | 'warning' | 'danger',
  loading: false,
  action: () => {}
});

const { add: addNotif } = useNotifications();

import { useAuth } from '../core/useAuth';
const { logout: authLogout } = useAuth();
const { push, updateLast, trimToIndex, consumeReset, trail } = useBreadcrumbs();

const breadcrumbs = computed(() => trail.value);

const getNameField = () => {
    return formMetadata.value?.rec_name || 'id';
};

const bcPush = (item: { label: string, path: string, query?: any, view?: 'list' | 'form', id?: any, domain?: any }) => {
    // IMPORTANT: Store the path WITHOUT query parameters for proper comparison
    // The query is stored separately in the query field
    const cleanQuery = { ... (item.query || {}) };
    delete cleanQuery.domain; 

    
    push({
        ...item,
        path: item.path, // Use the clean path without query string
        query: cleanQuery,
        domain: item.domain 
    });
};

const getDefaultFilterNames = (metadata: any): string[] => {
  const availableFilters = metadata?.search_config?.filters || [];
  return availableFilters
    .filter((filter: any) => filter?.default)
    .map((filter: any) => filter.name)
    .filter(Boolean);
};

const handleBreadcrumbClick = (bc: any, index: number) => {
  
  trimToIndex(index);
  router.push({
    path: bc.path,
    query: bc.query || {}
  });
};

const refreshList = async (params: { 
    search?: string, 
    searchField?: string, 
    domain?: string, 
    filters?: any[], 
    groupBy?: string, 
    offset?: number 
} = {}, updateUrl = false) => {
    if (params.search !== undefined) {
        currentSearch.value = params.search;
        currentOffset.value = 0; // Reset pagination on search
    }
    if (params.searchField !== undefined) currentSearchField.value = params.searchField;
    if (params.domain !== undefined) currentDomain.value = params.domain;
    if (params.filters !== undefined) {
        currentFilters.value = params.filters;
    }
    if (params.groupBy !== undefined) currentGroupBy.value = params.groupBy;
    if (params.offset !== undefined) currentOffset.value = params.offset;

    if (updateUrl) {
      const cleanQuery = { ...route.query };
      delete cleanQuery.domain; // Never put domain in URL

      // Use replace instead of push to update URL without creating new history entry
      router.replace({
        path: route.path,
        query: {
          ...cleanQuery,
          search: currentSearch.value || undefined,
          searchField: currentSearchField.value || undefined,
          filters: params.filters !== undefined ? JSON.stringify(currentFilters.value) : cleanQuery.filters,
          groupBy: currentGroupBy.value || undefined,
          offset: currentOffset.value || undefined
        }
      });
    }

    // Build domain from filters
    let combinedDomain = currentDomain.value;
    if (currentFilters.value.length > 0) {
        const filterDomain = buildDomainFromFilters(currentFilters.value);
        if (combinedDomain) {
            // Combine existing domain with filter domain
            const existingDomain = JSON.parse(combinedDomain);
            combinedDomain = JSON.stringify([...existingDomain, ...filterDomain]);
        } else {
            combinedDomain = JSON.stringify(filterDomain);
        }
    }

    await fetchItems({
        search: currentSearch.value,
        searchField: currentSearchField.value,
        domain: combinedDomain,
        filters: currentFilters.value,
        groupBy: currentGroupBy.value,
        limit: pageSize,
        offset: currentOffset.value
    });
};

const handleGlobalLogout = () => {
  authLogout();
  router.push('/login');
};

const init = async () => {
  
  // Consume reset flag (e.g. from sidebar click)
  if (consumeReset()) {
    // Reset consumed
  }

  // Optimization: If we just saved a new record and redirected to it, we already have the data in formData.
  // This prevents the "whole screen flicker" by skipping redundant fetches and transition loading.
  const currentId = formData.id;
  const targetId = props.initialId && props.initialId !== 'new' ? parseInt(props.initialId) : null;
  
  if (viewMode.value === 'form' && targetId && currentId === targetId) {
    if (trail.value.length === 0) {
        // Even if optimized, we need breadcrumbs if they were cleared
        const name = formData[getNameField()] || `#${formData.id}`;
        bcPush({ label: props.title, path: `/models/${props.model}`, view: 'list' });
        bcPush({ label: name, path: `/models/${props.model}/${formData.id}`, view: 'form', id: formData.id });
    }
    return;
  }

  try {
    const hasFiltersInUrl = route.query.filters !== undefined;

    // Read state: Prioritize breadcrumb domain over URL (which we are cleaning up anyway)
    currentSearch.value = (route.query.search as string) || '';
    currentSearchField.value = (route.query.searchField as string) || '';
    currentOffset.value = parseInt(route.query.offset as string) || 0;
    
    // Restore filters from URL
    if (route.query.filters) {
      try {
        const filtersFromUrl = JSON.parse(route.query.filters as string);
        currentFilters.value = Array.isArray(filtersFromUrl) ? filtersFromUrl : [];
      } catch (e) {
        currentFilters.value = [];
      }
    } else {
      currentFilters.value = [];
    }
    
    // Restore groupBy from URL
    currentGroupBy.value = (route.query.groupBy as string) || '';

    // Recover domain from the breadcrumb trail if it matches current path
    const activeBc = trail.value[trail.value.length - 1];
    if (activeBc && activeBc.domain) {
        currentDomain.value = typeof activeBc.domain === 'string' ? activeBc.domain : JSON.stringify(activeBc.domain);
    } else {
        currentDomain.value = (route.query.domain as string) || '';
    }

    if (props.initialId) {
      if (props.initialId === 'new') {
          viewMode.value = 'form';
          await fetchFormMeta();
          await formReset();
          
          // Only push the List breadcrumb if the trail is empty
          if (trail.value.length === 0) {
            const listLabel = formMetadata.value?.description || props.title;
            
            // Build query object with current filters, search, and groupBy
            const listQuery: any = {};
            if (currentSearch.value) listQuery.search = currentSearch.value;
            if (currentSearchField.value) listQuery.searchField = currentSearchField.value;
            if (currentFilters.value.length > 0) listQuery.filters = JSON.stringify(currentFilters.value);
            if (currentGroupBy.value) listQuery.groupBy = currentGroupBy.value;
            if (currentOffset.value) listQuery.offset = currentOffset.value.toString();
            
            bcPush({ 
              label: listLabel, 
              path: `/models/${props.model}`,
              query: listQuery,
              view: 'list' 
            });
          }
          bcPush({ 
            label: 'New', 
            path: `/models/${props.model}/new`, 
            view: 'form', 
            id: 'new',
            domain: currentDomain.value // Preserve current domain context
          });
          
          currentIndex.value = 0;
      } else {
          viewMode.value = 'form';
          await Promise.all([
            fetchFormMeta(),
            fetchListMeta()
          ]);
          if (!hasFiltersInUrl && currentFilters.value.length === 0) {
            currentFilters.value = getDefaultFilterNames(listMetadata.value);
          }
          // Fetch record and list in parallel for speed
          await Promise.all([
            fetchRecord(parseInt(props.initialId)),
            refreshList()
          ]);
          
          // Breadcrumb trail logic: 
          // If we have nothing in the trail, it means we navigated directly to this record (likely page refresh)
          if (trail.value.length === 0) {
            const listLabel = formMetadata.value?.description || props.title;
            
            // Build query object with current filters, search, and groupBy
            const listQuery: any = {};
            if (currentSearch.value) listQuery.search = currentSearch.value;
            if (currentSearchField.value) listQuery.searchField = currentSearchField.value;
            if (currentFilters.value.length > 0) listQuery.filters = JSON.stringify(currentFilters.value);
            if (currentGroupBy.value) listQuery.groupBy = currentGroupBy.value;
            if (currentOffset.value) listQuery.offset = currentOffset.value.toString();
            
            bcPush({ 
              label: listLabel, 
              path: `/models/${props.model}`,
              query: listQuery,
              view: 'list' 
            });
          }
          
          const recordName = formData[getNameField()] || `#${formData.id}`;
          
          // Znova Logic: If we are navigating via pager (Next/Prev), 
          // we should replace the last breadcrumb instead of appending.
          // We can detect this if the last breadcrumb is also a form of the same model.
          const lastBc = trail.value[trail.value.length - 1];
          if (lastBc && lastBc.view === 'form' && lastBc.path.includes(`/models/${props.model}/`)) {
              updateLast({
                  label: recordName,
                  path: router.resolve({ path: `/models/${props.model}/${formData.id}`, query: route.query }).fullPath,
                  id: formData.id,
                  domain: currentDomain.value
              });
          } else {
              bcPush({
                label: recordName,
                path: `/models/${props.model}/${formData.id}`,
                view: 'form',
                id: formData.id,
                domain: currentDomain.value
              });
          }
          
          // Find current index in listItems
          const idx = listItems.value.findIndex((item: any) => item.id === parseInt(props.initialId!));
          if (idx !== -1) {
            currentIndex.value = idx;
          } else {
            // Record ID not found in current page items. Defaulting to 0.
            currentIndex.value = 0;
          }
      }
    } else {
      // List View
      viewMode.value = 'list';
      const currentDomainParsed = currentDomain.value ? JSON.parse(currentDomain.value) : [];
      
      await fetchListMeta();
      if (!hasFiltersInUrl && currentFilters.value.length === 0) {
        currentFilters.value = getDefaultFilterNames(listMetadata.value);
      }
      const listLabel = listMetadata.value?.description || props.title;
      
      // Build query object with current filters, search, and groupBy
      const listQuery: any = {};
      if (currentSearch.value) listQuery.search = currentSearch.value;
      if (currentSearchField.value) listQuery.searchField = currentSearchField.value;
      if (currentFilters.value.length > 0) listQuery.filters = JSON.stringify(currentFilters.value);
      if (currentGroupBy.value) listQuery.groupBy = currentGroupBy.value;
      if (currentOffset.value) listQuery.offset = currentOffset.value.toString();
      
      
      bcPush({ 
          label: listLabel, 
          path: `/models/${props.model}`, 
          query: listQuery,
          view: 'list', 
          domain: currentDomainParsed 
      });
      await refreshList();
    }
  } catch (error) {
    // Handle initialization errors silently
  }
};

const handleNav = (direction: 'prev' | 'next') => {
  if (listItems.value.length === 0) return;
  
  let newIdx = currentIndex.value;
  if (direction === 'next') {
    newIdx = (currentIndex.value + 1) % listItems.value.length;
  } else {
    newIdx = (currentIndex.value - 1 + listItems.value.length) % listItems.value.length;
  }
  
  const targetId = listItems.value[newIdx].id;
  
  const cleanQuery = { ...route.query };
  delete cleanQuery.domain;

  // Since we are just navigating between records in the SAME set,
  // we don't want to push a new breadcrumb level.
  // Instead, the next init() call will see that we already have a trail 
  // and will use bcPush which handles the replacement if path/domain match.
  // Wait, if path changes (/1 -> /2), bcPush will append.
  // We want it to REPLACE the last item.
  
  router.push({
    path: `/models/${props.model}/${targetId}`,
    query: cleanQuery
  });
};

const handleView = (id: number) => {
  const cleanQuery = { ...route.query };
  delete cleanQuery.domain;

  router.push({
    path: `/models/${props.model}/${id}`,
    query: cleanQuery
  });
};

const handleCreate = () => {
  const cleanQuery = { ...route.query };
  delete cleanQuery.domain;

  router.push({
    path: `/models/${props.model}/new`,
    query: cleanQuery
  });
};

const handleSearch = (searchData: { query: string, field: string }) => {
    // Preserve current filters and groupBy when searching
    refreshList({ 
        search: searchData.query, 
        searchField: searchData.field,
        filters: currentFilters.value,
        groupBy: currentGroupBy.value
    }, true);
};

const handleFilter = (filters: any[]) => {
    // Convert filter objects to filter names for the new system
    const filterNames = filters.map(f => f.name || f);
    // Preserve current search and groupBy when filtering
    refreshList({ 
        filters: filterNames,
        search: currentSearch.value,
        searchField: currentSearchField.value,
        groupBy: currentGroupBy.value
    }, true);
};

const handleGroupBy = (groupBy: string) => {
    // Preserve current search and filters when grouping
    refreshList({ 
        groupBy,
        search: currentSearch.value,
        searchField: currentSearchField.value,
        filters: currentFilters.value
    }, true);
};

const buildDomainFromFilters = (filters: any[]): any[] => {
    // For the new system, filters are filter names that reference predefined filters
    // The backend now handles these names directly in list_records
    return [];
};

const handlePaginate = (offset: number) => {
    refreshList({ offset }, true);
};

const handleSave = async (payload?: any, callback?: () => void) => {
  await save(payload);
  if (!formError.value) {
    // Update breadcrumb name if it was "New"
    const newName = formData[getNameField()] || `#${formData.id}`;
    
    const cleanQuery = { ...route.query };
    delete cleanQuery.domain;
    
    const resolved = router.resolve({ path: `/models/${props.model}/${formData.id}`, query: cleanQuery });
    updateLast({ 
        label: newName, 
        path: resolved.fullPath, 
        id: formData.id,
        domain: currentDomain.value // Ensure domain is kept after save
    });

    // If it was a new record, we should redirect to its detail page
    if (props.initialId === 'new' && formData.id) {
       router.push({
         path: `/models/${props.model}/${formData.id}`,
         query: route.query
       });
    } else {
       // For existing records, refresh the data to get any server-side updates
       if (formData.id) {
         await fetchRecord(formData.id);
       }
    }

    // Execute callback if present (e.g. for auto-save before action)
    if (callback && typeof callback === 'function') {
        callback();
    }
  }
};

const handleCancel = () => {
  if (breadcrumbs.value.length > 1) {
    const previousBc = breadcrumbs.value[breadcrumbs.value.length - 2];
    handleBreadcrumbClick(previousBc, breadcrumbs.value.length - 2);
  } else {
    router.push({
      path: `/models/${props.model}`,
      query: route.query
    });
  }
};

const processServerAction = async (action: any) => {
  if (!action) return;

  // Handle dialog actions from backend
  if (action.type === 'ir.actions.dialog') {
    if (action.dialog_type === 'alert') {
      await alert({
        title: action.title || 'Alert',
        message: action.message,
        type: action.alert_type || 'info',
        confirmText: action.confirmText || 'OK'
      });
      
      // Process next action if provided
      if (action.on_confirm) {
        if (action.on_confirm.method) {
          // Call the method on the current record
          try {
            const resp = await api.post(`/models/${props.model}/${props.initialId}/call/${action.on_confirm.method}`, action.on_confirm.params || {});
            await processServerAction(resp.data);
          } catch (e: any) {
            const { handleApiError } = useErrorHandler();
            handleApiError(e);
          }
        } else if (action.on_confirm.action) {
          await processServerAction(action.on_confirm.action);
        }
      }
    } else if (action.dialog_type === 'confirm') {
      const confirmed = await confirm({
        title: action.title || 'Confirm',
        message: action.message,
        severity: action.severity || 'info',
        confirmText: action.confirmText || 'Confirm',
        cancelText: action.cancelText || 'Cancel'
      });
      
      if (confirmed && action.on_confirm) {
        if (action.on_confirm.method) {
          // Call the method on the current record
          try {
            const resp = await api.post(`/models/${props.model}/${props.initialId}/call/${action.on_confirm.method}`, action.on_confirm.params || {});
            await processServerAction(resp.data);
          } catch (e: any) {
            const { handleApiError } = useErrorHandler();
            handleApiError(e);
          }
        } else if (action.on_confirm.action) {
          await processServerAction(action.on_confirm.action);
        }
      } else if (!confirmed && action.on_cancel) {
        if (action.on_cancel.method) {
          try {
            const resp = await api.post(`/models/${props.model}/${props.initialId}/call/${action.on_cancel.method}`, action.on_cancel.params || {});
            await processServerAction(resp.data);
          } catch (e: any) {
            const { handleApiError } = useErrorHandler();
            handleApiError(e);
          }
        } else if (action.on_cancel.action) {
          await processServerAction(action.on_cancel.action);
        }
      }
    } else if (action.dialog_type === 'prompt') {
      const value = await prompt({
        title: action.title || 'Input',
        message: action.message || '',
        placeholder: action.placeholder || 'Enter value...',
        defaultValue: action.defaultValue || '',
        inputType: action.inputType || 'text',
        required: action.required !== false,
        confirmText: action.confirmText || 'OK',
        cancelText: action.cancelText || 'Cancel'
      });
      
      if (value !== null && action.on_confirm) {
        if (action.on_confirm.method) {
          try {
            const params = { ...action.on_confirm.params, value };
            const resp = await api.post(`/models/${props.model}/${props.initialId}/call/${action.on_confirm.method}`, params);
            await processServerAction(resp.data);
          } catch (e: any) {
            const { handleApiError } = useErrorHandler();
            handleApiError(e);
          }
        }
      }
    }
    return;
  }

  if (action.type === 'ir.actions.act_window') {
    // Check for target='new' (Wizard/Popup)
    if (action.target === 'new') {
        await openWizard(action);
        return;
    }

    const query: any = {};
    if (action.domain) {
      query.domain = JSON.stringify(action.domain);
    }
    
    // Always call bcPush. The refined useBreadcrumbs.ts:push will handle 
    // circular navigation (truncating the trail) automatically.
    if (action.res_id) {
        // Direct to form view
        bcPush({
          label: action.name || `${action.res_model.charAt(0).toUpperCase() + action.res_model.slice(1)} #${action.res_id}`,
          path: `/models/${action.res_model}/${action.res_id}`,
          query,
          view: 'form',
          id: action.res_id,
          domain: action.domain
        });
        
        router.push({
          path: `/models/${action.res_model}/${action.res_id}`,
          query
        });
    } else {
        bcPush({
          label: action.name || action.res_model.charAt(0).toUpperCase() + action.res_model.slice(1),
          path: `/models/${action.res_model}`,
          query,
          view: 'list',
          domain: action.domain
        });
        
        const cleanQuery = { ...query };
        delete cleanQuery.domain;

        router.push({
          path: `/models/${action.res_model}`,
          query: cleanQuery
        });
    }
  } else if (action.type === 'ir.actions.client') {
    if (action.tag === 'reload') {
      // Refresh the current record data
      if (viewMode.value === 'form' && props.initialId && props.initialId !== 'new') {
        await fetchRecord(parseInt(props.initialId));
      }
    } else if (action.tag === 'display_notification') {
        const { handleAction: handleNotif } = useNotifications();
        handleNotif(action);

        if (action.params?.refresh) {
            if (viewMode.value === 'form' && props.initialId && props.initialId !== 'new') {
                await fetchRecord(parseInt(props.initialId));
            } else if (viewMode.value === 'list') {
                await refreshList();
            }
        }

        if (action.params?.next) {
            await processServerAction(action.params.next);
        }
    } else if (action.tag === 'close_wizard') {
        closeWizard();
        
        if (action.params?.refresh) {
            if (viewMode.value === 'form' && props.initialId && props.initialId !== 'new') {
                await fetchRecord(parseInt(props.initialId));
            } else if (viewMode.value === 'list') {
                await refreshList();
            }
        }
        
        if (action.params?.notification) {
            const { handleAction: handleNotif } = useNotifications();
            handleNotif({ 
                type: 'ir.actions.client', 
                tag: 'display_notification', 
                params: action.params.notification 
            });
        }
    } else if (action.tag === 'download_file') {
        const url = action.params?.url;
        const filename = action.params?.filename || 'download';
        if (!url) return;

        try {
            const response = await api.get(url, { responseType: 'blob' });
            const blobUrl = window.URL.createObjectURL(response.data);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(blobUrl);
        } catch (e: any) {
            const { handleApiError } = useErrorHandler();
            handleApiError(e);
        }
    }
  }
};

const handleWizardComplete = async (nextAction: any) => {
  // If the wizard returns a next action (e.g. notification), process it
  if (nextAction) {
    await processServerAction(nextAction);
  }
};

const handleAction = async (btn: any) => {
  if (btn.name === 'delete') {
      handleDeleteRequest();
      return;
  }
  if (btn.method && props.initialId !== 'new') {
    try {
      const resp = await api.post(`/models/${props.model}/${props.initialId}/call/${btn.method}`);
      await processServerAction(resp.data);
    } catch (e: any) {
      // Use proper error handling with dialog
      const { handleApiError } = useErrorHandler();
      handleApiError(e, () => {
        // Retry callback
        handleAction(btn);
      });
    }
  }
};

const handleDeleteRequest = () => {
    confirmState.show = true;
    confirmState.title = 'Delete Record';
    confirmState.message = 'Are you sure you want to delete this record? This action cannot be undone.';
    confirmState.severity = 'danger';
    confirmState.action = executeDelete;
};

const executeDelete = async () => {
    confirmState.loading = true;
    try {
        await api.delete(`/models/${props.model}/${props.initialId}`);
        confirmState.show = false;
        addNotif({
            title: 'Record Deleted',
            message: 'The record has been successfully deleted.',
            type: 'success',
            sticky: false
        });
        
        // Navigate back to list or previous breadcrumb
        if (breadcrumbs.value.length > 1) {
            handleCancel();
        } else {
            router.push(`/models/${props.model}`);
        }
    } catch (e: any) {
        // Use proper error handling with dialog
        const { handleApiError } = useErrorHandler();
        handleApiError(e, () => {
            // Retry callback
            executeDelete();
        });
    } finally {
        confirmState.loading = false;
    }
};

const handleBulkDeleteRequest = (ids: number[]) => {
    confirmState.show = true;
    confirmState.title = 'Delete Multiple Records';
    confirmState.message = `Are you sure you want to delete ${ids.length} selected records? This action cannot be undone.`;
    confirmState.severity = 'danger';
    confirmState.action = () => executeBulkDelete(ids);
};

const executeBulkDelete = async (ids: number[]) => {
    confirmState.loading = true;
    try {
        const resp = await api.post(`/models/${props.model}/bulk_delete`, { ids });
        confirmState.show = false;
        addNotif({
            title: 'Records Deleted',
            message: `${resp.data.count} records have been successfully deleted.`,
            type: 'success',
            sticky: false
        });
        
        // Refresh the list
        await refreshList();
    } catch (e: any) {
        // Use proper error handling with dialog
        const { handleApiError } = useErrorHandler();
        handleApiError(e, () => {
            // Retry callback
            executeBulkDelete(ids);
        });
    } finally {
        confirmState.loading = false;
    }
};

onMounted(() => {
  init();
});

// Watch for route changes, but skip init() if only query params changed on list view
const lastPath = ref('');
const lastId = ref('');

watch(() => [props.model, props.initialId as string, route.query], ([newModel, newId, newQuery], [oldModel, oldId, oldQuery]) => {
  const currentPath = `${newModel}/${(newId as string) || 'list'}`;
  const previousPath = `${oldModel}/${(oldId as string) || 'list'}`;
  
  
  // Only call init() if the path actually changed (model or id changed)
  // Don't call init() if only query parameters changed (filters, search, groupBy)
  if (currentPath !== previousPath) {
    lastPath.value = currentPath;
    lastId.value = (newId as string) || '';
    init();
  } else {
  }
}, { deep: true });
</script>

<style lang="scss" scoped>
@use "../styles/variables" as v;

.generic-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  /* Ensure dropdowns can extend beyond view bounds */
  position: relative;
}

.view-content-root {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: visible; /* Changed to allow dropdowns to extend beyond */
  width: 100%; /* Ensure full width */
}

.view-content-root > div {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
}

.detail-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  /* Ensure dropdowns can extend beyond container bounds */
  position: relative;
  z-index: 1;
}

.global-loader { display: none; } // Legacy removal
</style>
