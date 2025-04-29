declare module '../components/RefreshIndicator' {
  import React from 'react';
  
  export interface RefreshIndicatorProps {
    lastRefreshed: Date;
    isLoading: boolean;
    onRefresh: () => void;
  }
  
  const RefreshIndicator: React.FC<RefreshIndicatorProps>;
  export default RefreshIndicator;
}

declare module '../components/AgentStatusCard' {
  import React from 'react';
  import { Agent } from '../types/agent';
  
  export interface AgentStatusCardProps {
    agent: Agent;
    tasksCount: number;
  }
  
  const AgentStatusCard: React.FC<AgentStatusCardProps>;
  export default AgentStatusCard;
}

declare module '../components/TaskListItem' {
  import React from 'react';
  import { TaskSummary } from '../types/task';
  
  export interface TaskListItemProps {
    task: TaskSummary;
    index: number;
  }
  
  const TaskListItem: React.FC<TaskListItemProps>;
  export default TaskListItem;
} 