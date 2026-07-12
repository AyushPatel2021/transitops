import { ref, reactive } from 'vue';
import api from '../core/api';
import { useNotifications } from './useNotifications';

// Global wizard state (singleton to allow access from anywhere)
const wizardState = reactive({
  show: false,
  modelName: '',
  wizardId: 0,
  metadata: null as any,
  data: null as any,
  loading: false,
  preparing: false // New flag to show loading state before dialog opens
});

export function useWizard() {
  const error = ref<string | null>(null);
  const { add } = useNotifications(); 

  /**
   * Open a wizard dialog.
   * Dictionary expected: { res_model: 'model.name', context: {...} }
   */
  const openWizard = async (action: any) => {
    if (!action.res_model) {
      console.error('Wizard action missing res_model', action);
      return;
    }

    // Reset state but don't show dialog yet
    wizardState.modelName = action.res_model;
    wizardState.wizardId = 0;
    wizardState.metadata = null;
    wizardState.data = null;
    wizardState.loading = false;
    wizardState.preparing = true; // Show preparing state
    wizardState.show = false; // Don't show until data is ready
    error.value = null;

    try {
      // Create wizard record and get metadata
      const response = await api.post(`/models/${action.res_model}/wizard`, action.context || {});
      
      const result = response.data;
      wizardState.wizardId = result.wizard_id;
      wizardState.metadata = result.metadata;
      wizardState.data = result.data;
      wizardState.preparing = false;
      
      // Only show dialog after data is loaded
      wizardState.show = true;
      
    } catch (err: any) {
      console.error('Failed to open wizard:', err);
      error.value = err.response?.data?.detail || 'Failed to open wizard';
      // Use add as per the useNotifications pattern
      add({
        type: 'danger',
        message: error.value || 'Error opening wizard',
        title: 'Wizard Error',
        sticky: false
      });
      wizardState.preparing = false;
      closeWizard();
    }
  };

  const closeWizard = () => {
    wizardState.show = false;
    // Clearing data after animation would be better but simple for now
    setTimeout(() => {
      wizardState.modelName = '';
      wizardState.wizardId = 0;
      wizardState.metadata = null;
      wizardState.data = null;
      wizardState.loading = false;
      wizardState.preparing = false;
    }, 300);
  };

  return {
    wizardState,
    error,
    openWizard,
    closeWizard
  };
}
