import { create } from 'zustand';
import { Memory, MemorySearchRequest } from '../types/memory';
import { memoryApi } from '../api';
import { parseApiError, ApiErrorResponse } from '../utils/errors';

interface MemoryState {
  memories: Memory[];
  searchQuery: string;
  searchAgentId: string | null;
  isLoading: boolean;
  error: ApiErrorResponse | null;
  searchMemory: (params: MemorySearchRequest) => Promise<void>;
  setSearchQuery: (query: string) => void;
  setSearchAgentId: (agentId: string | null) => void;
  clearMemories: () => void;
}

export const useMemoryStore = create<MemoryState>((set, get) => ({
  memories: [],
  searchQuery: '',
  searchAgentId: null,
  isLoading: false,
  error: null,

  searchMemory: async (params: MemorySearchRequest): Promise<void> => {
    try {
      set({ 
        isLoading: true, 
        error: null,
        searchQuery: params.query,
        searchAgentId: params.agent_id
      });
      
      const response = await memoryApi.searchMemories(params);
      
      set({
        memories: response.memories,
        isLoading: false
      });
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
    }
  },

  setSearchQuery: (query: string): void => {
    set({ searchQuery: query });
  },

  setSearchAgentId: (agentId: string | null): void => {
    set({ searchAgentId: agentId });
  },

  clearMemories: (): void => {
    set({ memories: [], searchQuery: '' });
  }
})); 