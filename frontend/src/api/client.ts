import axios from 'axios';

/**
 * Reusable Axios client instance for Analytics Studio API communication.
 * Reads base URL from VITE_API_BASE_URL environment variable, defaulting to live Render backend.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://analytics-studio-backend.onrender.com',
  headers: {
    'Content-Type': 'application/json',
  },
});
