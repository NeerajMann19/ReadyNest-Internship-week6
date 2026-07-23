import axios from 'axios';

/**
 * Reusable Axios client instance for Analytics Studio API communication.
 * Reads base URL from VITE_API_BASE_URL environment variable, defaulting to http://localhost:8000.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});
