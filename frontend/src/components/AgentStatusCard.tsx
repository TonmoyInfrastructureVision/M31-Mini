import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import StatusBadge from './StatusBadge';
import { Agent } from '../types/agent';
import { slideInUp } from '../animations';
import * as Avatar from '@radix-ui/react-avatar';
import * as Tooltip from '@radix-ui/react-tooltip';
import * as Progress from '@radix-ui/react-progress';

interface AgentStatusCardProps {
  agent: Agent;
  tasksCount: number;
}

const AgentStatusCard = ({ 
  agent, 
  tasksCount 
}: AgentStatusCardProps): React.ReactElement => {
  const isActive = agent.status === 'running';
  const hasError = agent.status === 'error' || agent.status === 'terminated';
  
  const getAgentInitials = (name: string): string => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };
  
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'running': return 'bg-gradient-to-r from-blue-500 to-indigo-600';
      case 'error': return 'bg-gradient-to-r from-red-500 to-pink-600';
      case 'terminated': return 'bg-gradient-to-r from-red-600 to-red-800';
      case 'idle': return 'bg-gradient-to-r from-gray-500 to-gray-700';
      default: return 'bg-gradient-to-r from-green-500 to-emerald-600';
    }
  };
  
  const getTaskProgressValue = (status: string): number => {
    switch (status) {
      case 'completed': return 100;
      case 'executing': return 75;
      case 'planning': return 50;
      case 'reflecting': return 85;
      case 'pending': return 25;
      case 'failed':
      case 'cancelled':
      default: return 0;
    }
  };
  
  return (
    <motion.div
      variants={slideInUp}
      initial="hidden"
      animate="visible" 
      className="bg-white p-5 rounded-xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow duration-200"
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center">
          <Avatar.Root className={`inline-flex h-10 w-10 select-none items-center justify-center overflow-hidden rounded-lg ${getStatusColor(agent.status)}`}>
            <Avatar.Fallback className="text-white text-sm leading-none font-medium">
              {getAgentInitials(agent.name)}
            </Avatar.Fallback>
          </Avatar.Root>
          
          <div className="ml-3">
            <h3 className="font-semibold text-gray-900 truncate max-w-[150px]">{agent.name}</h3>
            <div className="mt-1">
              <StatusBadge status={agent.status} />
            </div>
          </div>
        </div>
        
        <Tooltip.Root>
          <Tooltip.Trigger asChild>
            <div className="rounded-full bg-blue-50 p-1.5 text-xs font-medium text-blue-700">
              {tasksCount}
            </div>
          </Tooltip.Trigger>
          <Tooltip.Portal>
            <Tooltip.Content className="bg-slate-900 text-white px-3 py-1 rounded text-xs" sideOffset={5}>
              Active Tasks
              <Tooltip.Arrow className="fill-slate-900" />
            </Tooltip.Content>
          </Tooltip.Portal>
        </Tooltip.Root>
      </div>
      
      {agent.model && (
        <div className="flex items-center mb-3 px-2 py-1 bg-slate-50 rounded-md">
          <span className="text-xs text-gray-500">Model:</span>
          <span className="ml-1 text-xs font-medium text-gray-700">{agent.model}</span>
        </div>
      )}
      
      {agent.current_task && (
        <div className="mb-4 p-3 rounded-lg bg-gradient-to-r from-slate-50 to-white border border-slate-100">
          <div className="text-xs text-gray-500 mb-1 flex justify-between">
            <span>Current Task</span>
            <StatusBadge status={agent.current_task.status} size="sm" />
          </div>
          <div className="mt-1 text-sm font-medium text-gray-900 truncate">
            {agent.current_task.goal}
          </div>
          <div className="mt-2">
            <Progress.Root 
              className="relative overflow-hidden bg-slate-200 rounded-full w-full h-1.5" 
              value={getTaskProgressValue(agent.current_task.status)}
            >
              <Progress.Indicator 
                className="w-full h-full transition-transform duration-500 ease-in-out bg-blue-600" 
                style={{ transform: `translateX(-${100 - getTaskProgressValue(agent.current_task.status)}%)` }} 
              />
            </Progress.Root>
          </div>
        </div>
      )}
      
      <div className="flex justify-end mt-3 space-x-3">
        <Link 
          href={`/agents/${agent.id}`} 
          className="text-xs px-3 py-1.5 border border-indigo-200 text-indigo-700 hover:bg-indigo-50 font-medium rounded-md transition-colors duration-150"
        >
          Details
        </Link>
        <Link 
          href={`/tasks?agent=${agent.id}`} 
          className="text-xs px-3 py-1.5 bg-indigo-600 text-white hover:bg-indigo-700 font-medium rounded-md transition-colors duration-150"
        >
          View Tasks
        </Link>
      </div>
    </motion.div>
  );
};

export default AgentStatusCard; 