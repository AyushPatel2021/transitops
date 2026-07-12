import axios from 'axios';

// Global flag to prevent multiple simultaneous logouts
let isLoggingOut = false;

// Dynamic API URL detection for production deployment
const getApiUrl = () => {
    // Check if we have an environment variable (production)
    const envApiUrl = import.meta.env.VITE_API_URL;
    if (envApiUrl) {
        return envApiUrl;
    }
    
    // Production domain detection
    const currentHost = window.location.hostname;
    const protocol = window.location.protocol;
    
    // If we're on localhost, use localhost
    if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
        return 'http://localhost:8000/api/v1';
    }
    
    // For production domains, use the same domain with /api/v1
    return `${protocol}//${currentHost}/api/v1`;
};

const api = axios.create({
    baseURL: getApiUrl(),
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
});

api.interceptors.request.use((config: any) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        // Handle network errors
        if (!error.response) {
            error.code = 'NETWORK_ERROR';
        }
        
        if (error.response && error.response.status === 401) {
            // Check if this is an auth-related endpoint (login, signup, etc.)
            // For these endpoints, we should NOT clear token - let the component handle the error
            const authEndpoints = ['/auth/login', '/auth/signup', '/auth/forgot-password', '/auth/reset-password'];
            const requestUrl = error.config?.url || '';
            const isAuthEndpoint = authEndpoints.some(endpoint => requestUrl.includes(endpoint));
            
            if (!isAuthEndpoint && !isLoggingOut) {
                // Prevent multiple simultaneous logout attempts
                isLoggingOut = true;
                
                // For non-auth endpoints, clear token and redirect to login
                // But don't do a hard reload - use the router instead
                
                localStorage.removeItem('token');
                
                // Try to use the user store to logout properly
                try {
                    const { useUserStore } = await import('../../stores/userStore');
                    const userStore = useUserStore();
                    await userStore.logout();
                } catch (storeError) {
                    
                } finally {
                    // Reset the flag after logout completes
                    setTimeout(() => {
                        isLoggingOut = false;
                    }, 1000);
                }
                
                // Redirect to login using router if available
                try {
                    const { useRouter } = await import('vue-router');
                    const router = useRouter();
                    router.push('/login');
                } catch (routerError) {
                    // Fallback to window location change (no reload)
                    window.location.href = '/login';
                }
            }
            // For auth endpoints, just reject the promise and let the component handle it
        }
        return Promise.reject(error);
    }
);

export default api;
