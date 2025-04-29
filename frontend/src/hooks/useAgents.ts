import { useState, useCallback } from 'react';
import { agentApi } from '../api';
import { Agent, AgentCreate, AgentUpdate, AgentListResponse } from '../types/agent';
import { parseApiError, ApiErrorResponse } from '../utils/errors';

export interface UseAgentsReturn {
  agents: Agent[];
  total: number;
  isLoading: boolean;
  error: ApiErrorResponse | null;
  fetchAgents: () => Promise<void>;
  createAgent: (data: AgentCreate) => Promise<Agent | null>;
  updateAgent: (id: string, data: AgentUpdate) => Promise<Agent | null>;
  deleteAgent: (id: string) => Promise<boolean>;
  getAgent: (id: string) => Promise<Agent | null>;
}

export const useAgents = (): UseAgentsReturn => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<ApiErrorResponse | null>(null);

  const fetchAgents = useCallback(async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await agentApi.getAgents();
      setAgents(response.agents);
      setTotal(response.total);
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createAgent = useCallback(async (data: AgentCreate): Promise<Agent | null> => {
    try {
      setIsLoading(true);
      setError(null);
      const agent = await agentApi.createAgent(data);
      setAgents(prev => [...prev, agent]);
      setTotal(prev => prev + 1);
      return agent;
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateAgent = useCallback(async (id: string, data: AgentUpdate): Promise<Agent | null> => {
    try {
      setIsLoading(true);
      setError(null);
      const updatedAgent = await agentApi.updateAgent(id, data);
      setAgents(prev => prev.map(agent => agent.id === id ? updatedAgent : agent));
      return updatedAgent;
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteAgent = useCallback(async (id: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      await agentApi.deleteAgent(id);
      setAgents(prev => prev.filter(agent => agent.id !== id));
      setTotal(prev => prev - 1);
      return true;
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getAgent = useCallback(async (id: string): Promise<Agent | null> => {
    try {
      setIsLoading(true);
      setError(null);
      return await agentApi.getAgent(id);
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    agents,
    total,
    isLoading,
    error,
    fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    getAgent
  };
}; 