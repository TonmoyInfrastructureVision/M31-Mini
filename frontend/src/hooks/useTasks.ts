import { useState, useCallback } from 'react';
import { taskApi } from '../api';
import { TaskCreate, TaskResponse, TaskSummary } from '../types/task';
import { parseApiError, ApiErrorResponse } from '../utils/errors';

export interface UseTasksReturn {
  tasks: TaskSummary[];
  isLoading: boolean;
  error: ApiErrorResponse | null;
  fetchTasks: (agentId: string) => Promise<void>;
  createTask: (data: TaskCreate) => Promise<TaskResponse | null>;
  getTask: (id: string) => Promise<TaskResponse | null>;
  cancelTask: (id: string) => Promise<boolean>;
}

export const useTasks = (): UseTasksReturn => {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<ApiErrorResponse | null>(null);

  const fetchTasks = useCallback(async (agentId: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await taskApi.getAgentTasks(agentId);
      setTasks(response.tasks);
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createTask = useCallback(async (data: TaskCreate): Promise<TaskResponse | null> => {
    try {
      setIsLoading(true);
      setError(null);
      const task = await taskApi.createTask(data);
      return task;
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getTask = useCallback(async (id: string): Promise<TaskResponse | null> => {
    try {
      setIsLoading(true);
      setError(null);
      return await taskApi.getTask(id);
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const cancelTask = useCallback(async (id: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      await taskApi.cancelTask(id);
      return true;
    } catch (err) {
      const parsedError = parseApiError(err);
      setError(parsedError);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    tasks,
    isLoading,
    error,
    fetchTasks,
    createTask,
    getTask,
    cancelTask
  };
}; 