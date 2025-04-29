import { apiRequest } from './client';
import { MemorySearchRequest, MemorySearchResponse } from '../types/memory';

export const memoryApi = {
  searchMemories: async (data: MemorySearchRequest): Promise<MemorySearchResponse> => {
    const response = await apiRequest<MemorySearchResponse>({
      method: 'POST',
      url: '/memories/search',
      data,
    });
    return response.data;
  }
}; 