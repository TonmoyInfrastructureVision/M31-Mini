import { create } from 'zustand';
import { TaskCreate, TaskResponse, TaskSummary } from '../types/task';
import { taskApi } from '../api';
import { parseApiError, ApiErrorResponse } from '../utils/errors';

interface TaskState {
  tasks: TaskSummary[];
  selectedTask: TaskResponse | null;
  isLoading: boolean;
  error: ApiErrorResponse | null;
  fetchTasks: (agentId: string) => Promise<void>;
  getTask: (id: string) => Promise<void>;
  createTask: (data: TaskCreate) => Promise<TaskResponse | null>;
  cancelTask: (id: string) => Promise<boolean>;
  setSelectedTask: (task: TaskResponse | null) => void;
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  selectedTask: null,
  isLoading: false,
  error: null,

  fetchTasks: async (agentId: string): Promise<void> => {
    try {
      set({ isLoading: true, error: null });
      const response = await taskApi.getAgentTasks(agentId);
      set({
        tasks: response.tasks,
        isLoading: false
      });
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
    }
  },

  getTask: async (id: string): Promise<void> => {
    try {
      set({ isLoading: true, error: null });
      const task = await taskApi.getTask(id);
      set({ selectedTask: task, isLoading: false });
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
    }
  },

  createTask: async (data: TaskCreate): Promise<TaskResponse | null> => {
    try {
      set({ isLoading: true, error: null });
      const task = await taskApi.createTask(data);
      return task;
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
      return null;
    } finally {
      set({ isLoading: false });
    }
  },

  cancelTask: async (id: string): Promise<boolean> => {
    try {
      set({ isLoading: true, error: null });
      await taskApi.cancelTask(id);
      set(state => ({
        tasks: state.tasks.map(task => 
          task.id === id 
            ? { ...task, status: 'cancelled' as const } 
            : task
        ),
        selectedTask: state.selectedTask?.id === id 
          ? { ...state.selectedTask, status: 'cancelled' as const } 
          : state.selectedTask,
        isLoading: false
      }));
      return true;
    } catch (err) {
      const parsedError = parseApiError(err);
      set({ error: parsedError, isLoading: false });
      return false;
    }
  },

  setSelectedTask: (task: TaskResponse | null): void => {
    set({ selectedTask: task });
  }
})); 