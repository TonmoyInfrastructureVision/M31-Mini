import { apiRequest } from './client';
import { Agent, AgentCreate, AgentResponse, AgentListResponse } from '../types/agent';

export const agentApi = {
  createAgent: async (data: AgentCreate): Promise<AgentResponse> => {
    const response = await apiRequest<AgentResponse>({
      method: 'POST',
      url: '/agents',
      data,
    });
    return response.data;
  },

  getAgents: async (): Promise<AgentListResponse> => {
    const response = await apiRequest<AgentListResponse>({
      method: 'GET',
      url: '/agents',
    });
    return response.data;
  },

  getAgent: async (id: string): Promise<AgentResponse> => {
    const response = await apiRequest<AgentResponse>({
      method: 'GET',
      url: `/agents/${id}`,
    });
    return response.data;
  },

  updateAgent: async (id: string, data: Partial<AgentCreate>): Promise<AgentResponse> => {
    const response = await apiRequest<AgentResponse>({
      method: 'PATCH',
      url: `/agents/${id}`,
      data,
    });
    return response.data;
  },

  deleteAgent: async (id: string): Promise<{ success: boolean }> => {
    const response = await apiRequest<{ success: boolean }>({
      method: 'DELETE',
      url: `/agents/${id}`,
    });
    return response.data;
  }
}; 