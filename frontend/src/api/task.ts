import { apiRequest } from './client';
import { TaskCreate, TaskResponse, TaskListResponse } from '../types/task';

export const taskApi = {
  createTask: async (data: TaskCreate): Promise<TaskResponse> => {
    const response = await apiRequest<TaskResponse>({
      method: 'POST',
      url: '/tasks',
      data
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  },

  getTask: async (id: string): Promise<TaskResponse> => {
    const response = await apiRequest<TaskResponse>({
      method: 'GET',
      url: `/tasks/${id}`
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  },

  cancelTask: async (id: string): Promise<{ success: boolean }> => {
    const response = await apiRequest<{ success: boolean }>({
      method: 'POST',
      url: `/tasks/${id}/cancel`
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  },

  getAgentTasks: async (agentId: string): Promise<TaskListResponse> => {
    const response = await apiRequest<TaskListResponse>({
      method: 'GET',
      url: `/agents/${agentId}/tasks`
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response.data;
  }
};