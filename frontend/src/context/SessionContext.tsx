import React, { createContext, useContext, useState, type ReactNode } from 'react';
import type { Dataset } from '../types';
import { apiClient } from '../api/client';

interface SessionContextType {
  sessionId: string | null;
  dataset: Dataset | null;
  loading: boolean;
  error: string | null;
  uploadDataset: (file: File) => Promise<void>;
  clearSession: () => void;
  clearError: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const uploadDataset = async (file: File) => {
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/dataset/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data && response.data.session_id && response.data.dataset) {
        setSessionId(response.data.session_id);
        setDataset(response.data.dataset);
      } else {
        throw new Error('Invalid response structure from backend');
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.message || err.message || 'Failed to upload dataset. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const clearSession = () => {
    setSessionId(null);
    setDataset(null);
    setError(null);
  };

  const clearError = () => {
    setError(null);
  };

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        dataset,
        loading,
        error,
        uploadDataset,
        clearSession,
        clearError,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};
