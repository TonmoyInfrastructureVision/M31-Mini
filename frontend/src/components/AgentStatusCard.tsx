import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import StatusBadge from './StatusBadge';
import { Agent } from '../types/agent';
import { slideInUp } from '../animations';

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
  
  return (
    <motion.div
      variants={slideInUp}
      initial="hidden"
      animate="visible" 
      className={`bg-white p-4 rounded-lg shadow-md border-l-4 ${
        isActive ? 'border-blue-500' : hasError ? 'border-red-500' : 'border-green-500'
      }`}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-medium text-gray-900 truncate max-w-[70%]">{agent.name}</h3>
        <StatusBadge status={agent.status} />
      </div>
      
      {agent.model && (
        <p className="text-sm text-gray-500 mb-3">
          <span className="font-medium">Model:</span> {agent.model}
        </p>
      )}

      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-gray-500">Active Tasks</span>
        <span className={`font-medium ${
          tasksCount > 0 ? 'text-blue-600' : 'text-gray-500'
        }`}>
          {tasksCount}
        </span>
      </div>
      
      {agent.current_task && (
        <div className="mb-3">
          <div className="text-sm text-gray-500">Current Task:</div>
          <div className="mt-1 text-xs font-medium text-gray-900 truncate">
            {agent.current_task.goal}
          </div>
          <div className="mt-1 text-xs">
            <StatusBadge status={agent.current_task.status} size="sm" />
          </div>
        </div>
      )}
      
      <div className="flex justify-end mt-3 space-x-2">
        <Link 
          href={`/agents/${agent.id}`} 
          className="text-xs text-primary-600 hover:text-primary-900 font-medium"
        >
          Details
        </Link>
        <Link 
          href={`/tasks?agent=${agent.id}`} 
          className="text-xs text-primary-600 hover:text-primary-900 font-medium"
        >
          Tasks
        </Link>
      </div>
    </motion.div>
  );
};

export default AgentStatusCard; 