import { create } from 'zustand';
import { Agent, AgentCreate, AgentUpdate } from '../types/agent';
import { agentApi } from '../api';
import { parseApiError, ApiErrorResponse } from '../utils/errors';

interface AgentState {
  agents: Agent[];
  selectedAgent: Agent | null;
  total: number;
  isLoading: boolean;
  error: ApiErrorResponse | null;
  fetchAgents: () => Promise<void>;
  getAgent: (id: string) => Promise<void>;
  createAgent: (data: AgentCreate) => Promise<Agent | null>;
  updateAgent: (id: string, data: AgentUpdate) => Promise<Agent | null>;
  deleteAgent: (id: string) => Promise<boolean>;
  setSelectedAgent: (agent: Agent | null) => void;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: [],
  selectedAgent: null,
  total: 0,
  isLoading: false,
  error: null,

  fetchAgents: async (): Promise<void> => {
    try {
      set({ isLoading: true, error: null });
      const response = await agentApi.getAgents();
      set({
        agents: response.agents,
        total: response.total,
        isLoading: false
      });
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
    }
  },

  getAgent: async (id: string): Promise<void> => {
    try {
      set({ isLoading: true, error: null });
      const agent = await agentApi.getAgent(id);
      set({ selectedAgent: agent, isLoading: false });
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
    }
  },

  createAgent: async (data: AgentCreate): Promise<Agent | null> => {
    try {
      set({ isLoading: true, error: null });
      const agent = await agentApi.createAgent(data);
      set(state => ({
        agents: [...state.agents, agent],
        total: state.total + 1,
        isLoading: false
      }));
      return agent;
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
      return null;
    }
  },

  updateAgent: async (id: string, data: AgentUpdate): Promise<Agent | null> => {
    try {
      set({ isLoading: true, error: null });
      const updatedAgent = await agentApi.updateAgent(id, data);
      set(state => ({
        agents: state.agents.map(agent => agent.id === id ? updatedAgent : agent),
        selectedAgent: state.selectedAgent?.id === id ? updatedAgent : state.selectedAgent,
        isLoading: false
      }));
      return updatedAgent;
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
      return null;
    }
  },

  deleteAgent: async (id: string): Promise<boolean> => {
    try {
      set({ isLoading: true, error: null });
      await agentApi.deleteAgent(id);
      set(state => ({
        agents: state.agents.filter(agent => agent.id !== id),
        total: state.total - 1,
        selectedAgent: state.selectedAgent?.id === id ? null : state.selectedAgent,
        isLoading: false
      }));
      return true;
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
      return false;
    }
  },

  setSelectedAgent: (agent: Agent | null): void => {
    set({ selectedAgent: agent });
  }
})); 