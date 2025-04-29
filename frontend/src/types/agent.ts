import { TaskStatus, TaskSummary } from './task';

export interface Agent {
  id: string;
  name: string;
  description?: string;
  model?: string;
  workspace_dir?: string;
  status: AgentStatus;
  created_at: string;
  updated_at: string;
  current_task?: TaskSummary;
}

export interface AgentCreate {
  name: string;
  description?: string;
  model?: string;
  workspace_dir?: string;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  model?: string;
  workspace_dir?: string;
  status?: AgentStatus;
}

export enum AgentStatus {
  IDLE = 'idle',
  RUNNING = 'running',
  ERROR = 'error',
  TERMINATED = 'terminated'
}

export interface AgentResponse extends Agent {}

export interface AgentListResponse {
  agents: Agent[];
  total: number;
}