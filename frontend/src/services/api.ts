import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    // Don't set default Content-Type - let axios determine it based on request data
    // For JSON: axios auto-sets 'application/json'
    // For FormData: axios auto-sets 'multipart/form-data' with boundary
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add auth token to requests
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error: AxiosError) => {
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

            // Return structured error
            return Promise.reject({
                status,
                message: (data as any)?.error?.message || 'An error occurred',
                data
            });
        } else if (error.request) {
            // Request made but no response received
            console.error('No response from server');
            return Promise.reject({
                status: 0,
                message: 'Network error - please check your connection'
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
