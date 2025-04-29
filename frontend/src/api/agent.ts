import { apiRequest } from './client';
import { Agent, AgentCreate, AgentListResponse, AgentUpdate } from '../types/agent';

export const agentApi = {
  getAgents: async (): Promise<AgentListResponse> => {
    const response = await apiRequest<AgentListResponse>({
      method: 'GET',
      url: '/agents'
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  },

  getAgent: async (id: string): Promise<Agent> => {
    const response = await apiRequest<Agent>({
      method: 'GET',
      url: `/agents/${id}`
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  },

  createAgent: async (data: AgentCreate): Promise<Agent> => {
    const response = await apiRequest<Agent>({
      method: 'POST',
      url: '/agents',
      data
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  },

  updateAgent: async (id: string, data: AgentUpdate): Promise<Agent> => {
    const response = await apiRequest<Agent>({
      method: 'PATCH',
      url: `/agents/${id}`,
      data
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  },

  deleteAgent: async (id: string): Promise<void> => {
    const response = await apiRequest<void>({
      method: 'DELETE',
      url: `/agents/${id}`
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
  }
}; 