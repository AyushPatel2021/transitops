import { reactive } from 'vue';
import { useNotifications } from './useNotifications';

export interface ErrorData {
  error_type: string;
  title: string;
  message: string;
  details?: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  humorous_message?: string;
  suggestions?: string[];
  error_code?: string;
  field_errors?: Record<string, string>;
  show_dialog: boolean;
}

export interface ErrorDialogState {
  show: boolean;
  error: ErrorData | null;
  retryable: boolean;
  retryCallback?: () => void;
}

const errorDialogState = reactive<ErrorDialogState>({
  show: false,
  error: null,
  retryable: false,
  retryCallback: undefined
});

export function useErrorHandler() {
  const { add: addNotification } = useNotifications();

  const showErrorDialog = (
    error: ErrorData, 
    retryCallback?: () => void
  ) => {
    errorDialogState.error = error;
    errorDialogState.show = true;
    errorDialogState.retryable = !!retryCallback;
    errorDialogState.retryCallback = retryCallback;
  };

  const closeErrorDialog = () => {
    errorDialogState.show = false;
    errorDialogState.error = null;
    errorDialogState.retryable = false;
    errorDialogState.retryCallback = undefined;
  };

  const retryAction = () => {
    if (errorDialogState.retryCallback) {
      errorDialogState.retryCallback();
    }
    closeErrorDialog();
  };

  const reportError = (errorReport: any) => {
    // Here you could send the error report to your logging service
    // For now, we'll just show a notification
    addNotification({
      title: 'Error Reported',
      message: 'Thank you for reporting this issue. Our team has been notified.',
      type: 'success',
      sticky: false
    });
  };

  const handleApiError = (error: any, retryCallback?: () => void) => {
    // Check if the error response contains enhanced error information
    if (error.response?.data?.error) {
      const errorData = error.response.data.error as ErrorData;
      showErrorDialog(errorData, retryCallback);
      return;
    }

    // Fallback to creating error based on HTTP status and message
    const status = error.response?.status;
    const message = error.response?.data?.detail || error.message || 'An unexpected error occurred';

    let errorData: ErrorData;

    switch (status) {
      case 400:
        errorData = createUserError(message);
        break;
      case 401:
        errorData = createAuthenticationError(message);
        break;
      case 403:
        errorData = createAccessError(message);
        break;
      case 404:
        errorData = createNotFoundError(message);
        break;
      case 422:
        errorData = createValidationError(message, error.response?.data?.field_errors);
        break;
      case 429:
        errorData = createRateLimitError(message);
        break;
      case 500:
      case 502:
      case 503:
      case 504:
        errorData = createServerError(message);
        break;
      default:
        if (error.code === 'NETWORK_ERROR' || error.code === 'ERR_NETWORK') {
          errorData = createNetworkError(message);
        } else {
          errorData = createGenericError(message);
        }
    }

    // Always show dialog for all errors since we have proper error dialogs now
    showErrorDialog(errorData, retryCallback);
  };

  // Error factory functions
  const createUserError = (message: string): ErrorData => ({
    error_type: 'user_error',
    title: 'User Error',
    message,
    severity: 'warning',
    humorous_message: getRandomHumorousMessage('user_error'),
    suggestions: [
      'Double-check your input',
      'Try a different approach',
      'Contact support if you need help'
    ],
    show_dialog: true
  });

  const createValidationError = (message: string, fieldErrors?: Record<string, string>): ErrorData => ({
    error_type: 'validation_error',
    title: 'Validation Error',
    message,
    severity: 'warning',
    humorous_message: getRandomHumorousMessage('validation_error'),
    field_errors: fieldErrors,
    suggestions: [
      'Check all required fields',
      'Ensure data formats are correct',
      'Review any highlighted field errors'
    ],
    show_dialog: true
  });

  const createAccessError = (message: string): ErrorData => ({
    error_type: 'access_error',
    title: 'Access Denied',
    message,
    severity: 'error',
    humorous_message: getRandomHumorousMessage('access_error'),
    suggestions: [
      'Contact your administrator',
      'Check if you have the required permissions',
      'Try logging out and back in'
    ],
    show_dialog: true
  });

  const createAuthenticationError = (message: string): ErrorData => ({
    error_type: 'authentication_error',
    title: 'Authentication Required',
    message,
    severity: 'error',
    humorous_message: getRandomHumorousMessage('authentication_error'),
    suggestions: [
      'Check your username and password',
      'Try logging out and back in',
      'Contact support if the problem persists'
    ],
    show_dialog: true
  });

  const createServerError = (message: string): ErrorData => ({
    error_type: 'server_error',
    title: 'Server Error',
    message,
    severity: 'critical',
    humorous_message: getRandomHumorousMessage('server_error'),
    suggestions: [
      'Try refreshing the page',
      'Wait a moment and try again',
      'Contact support if the issue persists'
    ],
    show_dialog: true
  });

  const createNetworkError = (message: string): ErrorData => ({
    error_type: 'network_error',
    title: 'Connection Error',
    message,
    severity: 'error',
    humorous_message: getRandomHumorousMessage('network_error'),
    suggestions: [
      'Check your internet connection',
      'Try refreshing the page',
      'Wait a moment and try again'
    ],
    show_dialog: true
  });

  const createNotFoundError = (message: string): ErrorData => ({
    error_type: 'not_found_error',
    title: 'Not Found',
    message,
    severity: 'warning',
    humorous_message: getRandomHumorousMessage('not_found_error'),
    suggestions: [
      'Check the URL or resource ID',
      'Make sure the resource exists',
      'Try going back and starting over'
    ],
    show_dialog: true
  });

  const createRateLimitError = (message: string): ErrorData => ({
    error_type: 'rate_limit_error',
    title: 'Rate Limit Exceeded',
    message,
    severity: 'warning',
    humorous_message: getRandomHumorousMessage('rate_limit_error'),
    suggestions: [
      'Wait a moment before trying again',
      'Slow down your requests',
      'Try again in a few minutes'
    ],
    show_dialog: true
  });

  const createGenericError = (message: string): ErrorData => ({
    error_type: 'user_error',
    title: 'Error',
    message,
    severity: 'error',
    humorous_message: getRandomHumorousMessage('user_error'),
    suggestions: [
      'Try refreshing the page',
      'Wait a moment and try again',
      'Contact support if needed'
    ],
    show_dialog: true
  });

  // Humorous messages (simplified version for frontend)
  const humorousMessages = {
    user_error: [
      "Oops! Looks like someone's having a case of the Mondays! 🤦‍♂️",
      "Well, that didn't go as planned... Time for Plan B! 🎭",
      "Houston, we have a problem... but it's totally fixable! 🚀",
      "Whoopsie-daisy! Let's try that again, shall we? 🌼"
    ],
    validation_error: [
      "Your data is playing hard to get! Let's make it happy! 💕",
      "Validation says 'Nope!' - but we can fix this together! ✋",
      "The form police have some concerns about your input! 👮‍♂️",
      "Your data needs a little TLC before it can proceed! 🛠️"
    ],
    access_error: [
      "Access denied! You shall not pass... without proper permissions! 🧙‍♂️",
      "This area is VIP only - time to upgrade your membership! 💎",
      "Looks like you're trying to peek behind the curtain! 🎭",
      "Sorry, this feature is playing hard to get! 💅"
    ],
    network_error: [
      "The internet seems to be taking a coffee break! ☕",
      "Network gremlins are at it again! 👹",
      "Your connection is playing hide and seek! 🙈",
      "The tubes of the internet are a bit clogged right now! 🚰"
    ],
    server_error: [
      "Our server is having an existential crisis! 🤖",
      "Something went wrong in the digital realm! ⚡",
      "The server hamsters need a quick snack break! 🐹",
      "Our backend is doing its best impression of a confused penguin! 🐧"
    ],
    not_found_error: [
      "404: This page went on vacation and forgot to leave a note! 🏖️",
      "We looked everywhere, but this content is playing hide and seek! 🔍",
      "This page has vanished like socks in a washing machine! 🧦",
      "Error 404: Content not found, but your sense of humor is intact! 😄"
    ],
    rate_limit_error: [
      "Whoa there, speed racer! Let's take it down a notch! 🏎️",
      "You're moving faster than a caffeinated cheetah! ☕🐆",
      "Slow down, turbo! Even The Flash takes breaks! ⚡",
      "Easy there, tiger! Rome wasn't built in a day! 🏛️"
    ],
    authentication_error: [
      "Who goes there? State your name and password! 🛡️",
      "Authentication failed: Are you who you say you are? 🕵️‍♂️",
      "Login error: Your credentials are having an identity crisis! 🎭",
      "Access denied: You're not on the guest list! 📋"
    ]
  };

  const getRandomHumorousMessage = (errorType: string): string => {
    const messages = humorousMessages[errorType as keyof typeof humorousMessages] || humorousMessages.user_error;
    return messages[Math.floor(Math.random() * messages.length)];
  };

  return {
    errorDialogState,
    showErrorDialog,
    closeErrorDialog,
    retryAction,
    reportError,
    handleApiError,
    createUserError,
    createValidationError,
    createAccessError,
    createAuthenticationError,
    createServerError,
    createNetworkError,
    createNotFoundError,
    createRateLimitError
  };
}