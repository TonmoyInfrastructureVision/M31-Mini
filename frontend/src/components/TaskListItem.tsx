import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import StatusBadge from './StatusBadge';
import { TaskSummary } from '../types/task';
import { listItemVariants } from '../animations';

interface TaskListItemProps {
  task: TaskSummary;
  index: number;
}

const TaskListItem = ({ 
  task, 
  index 
}: TaskListItemProps): React.ReactElement => {
  const formattedDate = new Date(task.created_at).toLocaleString();
  const isActiveTask = ['pending', 'planning', 'executing', 'reflecting'].includes(task.status);
  
  return (
    <motion.div
      variants={listItemVariants}
      initial="hidden"
      animate="visible" 
      transition={{ delay: index * 0.05 }}
      className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
    >
      <div className="flex justify-between items-start">
        <div className="max-w-[70%]">
          <h3 className="font-medium text-gray-900 truncate">{task.goal}</h3>
          <p className="text-xs text-gray-500 mt-1">{formattedDate}</p>
        </div>
        <StatusBadge status={task.status} />
      </div>
      
      <div className="flex justify-end mt-3">
        <Link 
          href={`/tasks/${task.id}`} 
          className="text-xs text-primary-600 hover:text-primary-900 font-medium inline-flex items-center"
        >
          <span>View Details</span>
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-3 w-3 ml-1" 
            viewBox="0 0 20 20" 
            fill="currentColor"
          >
            <path 
              fillRule="evenodd" 
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" 
              clipRule="evenodd" 
            />
          </svg>
        </Link>
      </div>
      
      {isActiveTask && (
        <motion.div 
          className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ 
            duration: 1.5, 
            repeat: Infinity, 
            ease: "easeInOut" 
          }}
        >
          <motion.div 
            className="h-full bg-blue-500 rounded-full"
            animate={{ 
              width: ['0%', '100%'],
              x: ['-100%', '0%'],
            }}
            transition={{ 
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        </motion.div>
      )}
    </motion.div>
  );
};

export default TaskListItem; 