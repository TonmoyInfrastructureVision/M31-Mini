import React, { ReactNode } from 'react';
import clsx from 'clsx';
import { AgentStatus } from '../types/agent';
import { TaskStatus } from '../types/task';

type StatusType = AgentStatus | TaskStatus | 'success' | 'error' | 'warning' | 'info';

interface StatusBadgeProps {
  status: StatusType;
  className?: string;
  children?: ReactNode;
}

export default function StatusBadge({ status, className, children }: StatusBadgeProps): React.ReactElement {
  const getStatusStyle = (status: StatusType): string => {
    // Agent statuses
    if (status === 'idle') return 'bg-green-100 text-green-800';
    if (status === 'running') return 'bg-blue-100 text-blue-800';
    if (status === 'error') return 'bg-red-100 text-red-800';
    if (status === 'terminated') return 'bg-gray-100 text-gray-800';
    
    // Task statuses
    if (status === 'pending') return 'bg-yellow-100 text-yellow-800';
    if (status === 'planning') return 'bg-indigo-100 text-indigo-800';
    if (status === 'executing') return 'bg-blue-100 text-blue-800';
    if (status === 'reflecting') return 'bg-purple-100 text-purple-800';
    if (status === 'completed') return 'bg-green-100 text-green-800';
    if (status === 'failed') return 'bg-red-100 text-red-800';
    if (status === 'cancelled') return 'bg-gray-100 text-gray-800';
    
    // Generic statuses
    if (status === 'success') return 'bg-green-100 text-green-800';
    if (status === 'warning') return 'bg-yellow-100 text-yellow-800';
    if (status === 'info') return 'bg-blue-100 text-blue-800';
    
    // Default
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <span
      className={clsx(
        'px-2 inline-flex text-xs leading-5 font-semibold rounded-full',
        getStatusStyle(status),
        className
      )}
    >
      {children || status}
    </span>
  );
} 