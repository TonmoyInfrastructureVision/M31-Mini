import { useState, useCallback } from 'react';
import { memoryApi } from '../api';
import { Memory, MemorySearchRequest } from '../types/memory';
import { parseApiError, ApiErrorResponse } from '../utils/errors';

export interface UseMemoryReturn {
  memories: Memory[];
  isLoading: boolean;
  error: ApiErrorResponse | null;
  searchMemory: (params: MemorySearchRequest) => Promise<Memory[]>;
}

export const useMemory = (): UseMemoryReturn => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<ApiErrorResponse | null>(null);

  const searchMemory = useCallback(async (params: MemorySearchRequest): Promise<Memory[]> => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await memoryApi.searchMemories(params);
      setMemories(response.memories);
      return response.memories;
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    memories,
    isLoading,
    error,
    searchMemory
  };
}; 