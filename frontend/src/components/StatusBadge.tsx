import React, { ReactNode } from 'react';
import clsx from 'clsx';
import { AgentStatus } from '../types/agent';
import { TaskStatus } from '../types/task';

type StatusType = AgentStatus | TaskStatus | 'success' | 'error' | 'warning' | 'info';
type BadgeSize = 'sm' | 'md' | 'lg';

interface StatusBadgeProps {
  status: StatusType;
  className?: string;
  children?: ReactNode;
  size?: BadgeSize;
}

export default function StatusBadge({ 
  status, 
  className, 
  children,
  size = 'md'
}: StatusBadgeProps): React.ReactElement {
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

  const getSizeStyles = (size: BadgeSize): string => {
    switch (size) {
      case 'sm':
        return 'px-1.5 py-0.5 text-[10px] leading-4';
      case 'lg':
        return 'px-3 py-1 text-sm leading-5';
      case 'md':
      default:
        return 'px-2 py-0.5 text-xs leading-5';
    }
  };

  return (
    <span
      className={clsx(
        'inline-flex font-semibold rounded-full',
        getStatusStyle(status),
        getSizeStyles(size),
        className
      )}
    >
      {children || status}
    </span>
  );
} 