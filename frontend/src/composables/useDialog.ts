import { reactive } from 'vue';

// Global dialog state
const alertState = reactive({
  show: false,
  title: '',
  message: '',
  type: 'info' as 'info' | 'success' | 'warning' | 'error',
  confirmText: 'OK',
  loading: false,
  onConfirm: () => {}
});

const confirmState = reactive({
  show: false,
  title: '',
  message: '',
  severity: 'info' as 'info' | 'warning' | 'danger',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  loading: false,
  onConfirm: () => {},
  onCancel: () => {}
});

const promptState = reactive({
  show: false,
  title: '',
  message: '',
  placeholder: 'Enter value...',
  defaultValue: '',
  inputType: 'text' as 'text' | 'number' | 'email' | 'password',
  required: true,
  confirmText: 'OK',
  cancelText: 'Cancel',
  loading: false,
  onConfirm: (value: string) => {},
  onCancel: () => {}
});

export function useDialog() {
  /**
   * Show an alert dialog
   * @param options Alert options
   * @returns Promise that resolves when user clicks OK
   */
  const alert = (options: {
    title?: string;
    message: string;
    type?: 'info' | 'success' | 'warning' | 'error';
    confirmText?: string;
  }): Promise<void> => {
    return new Promise((resolve) => {
      alertState.title = options.title || 'Alert';
      alertState.message = options.message;
      alertState.type = options.type || 'info';
      alertState.confirmText = options.confirmText || 'OK';
      alertState.loading = false;
      alertState.onConfirm = () => {
        alertState.show = false;
        resolve();
      };
      alertState.show = true;
    });
  };

  /**
   * Show a confirmation dialog
   * @param options Confirm options
   * @returns Promise that resolves to true if confirmed, false if cancelled
   */
  const confirm = (options: {
    title?: string;
    message: string;
    severity?: 'info' | 'warning' | 'danger';
    confirmText?: string;
    cancelText?: string;
  }): Promise<boolean> => {
    return new Promise((resolve) => {
      confirmState.title = options.title || 'Confirm';
      confirmState.message = options.message;
      confirmState.severity = options.severity || 'info';
      confirmState.confirmText = options.confirmText || 'Confirm';
      confirmState.cancelText = options.cancelText || 'Cancel';
      confirmState.loading = false;
      confirmState.onConfirm = () => {
        confirmState.show = false;
        resolve(true);
      };
      confirmState.onCancel = () => {
        confirmState.show = false;
        resolve(false);
      };
      confirmState.show = true;
    });
  };

  /**
   * Show a prompt dialog for user input
   * @param options Prompt options
   * @returns Promise that resolves to the input value, or null if cancelled
   */
  const prompt = (options: {
    title?: string;
    message?: string;
    placeholder?: string;
    defaultValue?: string;
    inputType?: 'text' | 'number' | 'email' | 'password';
    required?: boolean;
    confirmText?: string;
    cancelText?: string;
  }): Promise<string | null> => {
    return new Promise((resolve) => {
      promptState.title = options.title || 'Input';
      promptState.message = options.message || '';
      promptState.placeholder = options.placeholder || 'Enter value...';
      promptState.defaultValue = options.defaultValue || '';
      promptState.inputType = options.inputType || 'text';
      promptState.required = options.required !== false;
      promptState.confirmText = options.confirmText || 'OK';
      promptState.cancelText = options.cancelText || 'Cancel';
      promptState.loading = false;
      promptState.onConfirm = (value: string) => {
        promptState.show = false;
        resolve(value);
      };
      promptState.onCancel = () => {
        promptState.show = false;
        resolve(null);
      };
      promptState.show = true;
    });
  };

  /**
   * Close the alert dialog
   */
  const closeAlert = () => {
    alertState.show = false;
  };

  /**
   * Close the confirm dialog
   */
  const closeConfirm = () => {
    confirmState.show = false;
  };

  /**
   * Close the prompt dialog
   */
  const closePrompt = () => {
    promptState.show = false;
  };

  return {
    // States (for binding to components)
    alertState,
    confirmState,
    promptState,
    
    // Methods
    alert,
    confirm,
    prompt,
    closeAlert,
    closeConfirm,
    closePrompt
  };
}
