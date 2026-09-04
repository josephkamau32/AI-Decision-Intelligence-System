import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Cold start listener management for Render free tier (~50s cold start)
type WarmingListener = (isWarming: boolean) => void;
const warmingListeners = new Set<WarmingListener>();
let activeRequests = 0;
let warmingTimer: ReturnType<typeof setTimeout> | null = null;

export const subscribeBackendWarming = (listener: WarmingListener) => {
    warmingListeners.add(listener);
    return () => {
        warmingListeners.delete(listener);
    };
};

export const setBackendWarmingManually = (isWarming: boolean) => {
    warmingListeners.forEach(cb => cb(isWarming));
};

const onRequestStart = () => {
    activeRequests++;
    if (!warmingTimer) {
        // If request takes more than 3.5s, signal that backend is likely spinning up from sleep
        warmingTimer = setTimeout(() => {
            if (activeRequests > 0) {
                warmingListeners.forEach(cb => cb(true));
            }
        }, 3500);
    }
};

const onRequestEnd = () => {
    activeRequests = Math.max(0, activeRequests - 1);
    if (activeRequests === 0) {
        if (warmingTimer) {
            clearTimeout(warmingTimer);
            warmingTimer = null;
        }
        warmingListeners.forEach(cb => cb(false));
    }
};

// Create axios instance with default config (90s timeout for Render cold starts)
const api: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 90000,
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        onRequestStart();
        // Add auth token to requests
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error: AxiosError) => {
        onRequestEnd();
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        onRequestEnd();
        return response;
    },
    async (error: AxiosError) => {
        onRequestEnd();
        if (error.response) {
            // Server responded with error status
            const { status, data } = error.response;

            switch (status) {
                case 401:
                    // Handle unauthorized - redirect to login
                    console.error('Unauthorized access');
                    localStorage.removeItem('auth_token');
                    if (!window.location.pathname.includes('/login')) {
                        window.location.href = '/login';
                    }
                    break;
                case 403:
                    console.error('Forbidden access');
                    break;
                case 404:
                    console.error('Resource not found');
                    break;
                case 429:
                    console.error('Too many requests - rate limited');
                    break;
                case 500:
                    console.error('Internal server error');
                    break;
                default:
                    console.error(`API error: ${status}`);
            }

            // Extract error message safely from various backend error formats
            let errorMessage = 'An error occurred';
            if ((data as any)?.error?.message && typeof (data as any).error.message === 'string') {
                errorMessage = (data as any).error.message;
            } else if (typeof (data as any)?.detail === 'string') {
                errorMessage = (data as any).detail;
            } else if (Array.isArray((data as any)?.detail) && (data as any).detail.length > 0) {
                errorMessage = (data as any).detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
            } else if (typeof (data as any)?.message === 'string') {
                errorMessage = (data as any).message;
            }

            // Return structured error
            return Promise.reject({
                status,
                message: errorMessage,
                data
            });
        } else if (error.request) {
            // Request made but no response received
            console.error('No response from server');
            const isTimeout = error.code === 'ECONNABORTED' || error.message?.includes('timeout');
            return Promise.reject({
                status: 0,
                message: isTimeout
                    ? 'Connection timed out. If the backend was sleeping, it may take up to a minute to start. Please retry.'
                    : 'Network error - please check your connection or wait for backend to finish waking up.'
            });
        } else {
            // Something went wrong setting up the request
            console.error('Request setup error:', error.message);
            return Promise.reject({
                status: -1,
                message: error.message
            });
        }
    }
);

export default api;

// Export types for use in services
export type { AxiosError, AxiosRequestConfig };
