import axios from 'axios';

// Create axios instance
// baseURL is empty so requests use the current domain (which Vite server proxies)
export const api = axios.create({
  baseURL: '/',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    console.log('API request token:', token);
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle unauthorized error (e.g., token expired)
    if (error.response && error.response.status === 401) {
      // Do not redirect; let component handle auth errors
    }
    
    // Extract standard error message from API response
    const message = error.response?.data?.detail || 
                    error.response?.data?.message || 
                    error.message || 
                    'An unexpected error occurred';
                    
    error.errorMessage = message;
    return Promise.reject(error);
  }
);

export default api;
