export type TaskStatus = 'pending' | 'planning' | 'executing' | 'reflecting' | 'completed' | 'failed' | 'cancelled';

export interface TaskCreate {
  goal: string;
  agent_id: string;
}

export interface TaskResponse {
  id: string;
  agent_id: string;
  goal: string;
  status: TaskStatus;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  plan?: Plan;
  results?: TaskResult[];
  reflection?: Reflection;
  error?: string;
}

export interface TaskListResponse {
  agent_id: string;
  tasks: TaskSummary[];
}

export interface TaskSummary {
  id: string;
  goal: string;
  status: TaskStatus;
  created_at: string;
  success?: boolean;
}

export interface ExtendedTaskSummary extends TaskSummary {
  agent_id?: string;
  agentName?: string;
  updated_at?: string;
}

export interface Plan {
  id: string;
  goal: string;
  thought: string;
  created_at: string;
  steps: PlanStep[];
}

export interface PlanStep {
  id: number;
  description: string;
  tool?: string;
  tool_args?: Record<string, any>;
}

export interface TaskResult {
  step_id: number;
  success: boolean;
  result?: string;
  error?: string;
  tool_used?: string;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface Reflection {
  success: boolean;
  reasoning: string;
  learning: string;
  next_steps: string[];
}