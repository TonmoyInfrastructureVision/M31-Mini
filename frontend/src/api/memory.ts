import { apiRequest } from './client';
import { MemorySearchRequest, MemorySearchResponse } from '../types/memory';

export const memoryApi = {
  searchMemories: async (data: MemorySearchRequest): Promise<MemorySearchResponse> => {
    const response = await apiRequest<MemorySearchResponse>({
      method: 'POST',
      url: '/memories/search',
      data
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  },
  
  getAgentMemories: async (agentId: string, type?: string, limit?: number): Promise<MemorySearchResponse> => {
    const queryParams = new URLSearchParams();
    
    if (type) {
      queryParams.append('memory_type', type);
    }
    
    if (limit) {
      queryParams.append('limit', limit.toString());
    }
    
    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    
    const response = await apiRequest<MemorySearchResponse>({
      method: 'GET',
      url: `/agents/${agentId}/memories${queryString}`
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  }
}; 