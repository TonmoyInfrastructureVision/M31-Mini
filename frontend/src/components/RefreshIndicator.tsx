import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface RefreshIndicatorProps {
  lastRefreshed: Date;
  isLoading: boolean;
  onRefresh: () => void;
}

const RefreshIndicator = ({ 
  lastRefreshed, 
  isLoading, 
  onRefresh 
}: RefreshIndicatorProps): React.ReactElement => {
  const [timeAgo, setTimeAgo] = useState<string>('');
  
  useEffect(() => {
    const updateTimeAgo = (): void => {
      const seconds = Math.floor((new Date().getTime() - lastRefreshed.getTime()) / 1000);
      
      if (seconds < 60) {
        setTimeAgo(`${seconds} second${seconds !== 1 ? 's' : ''} ago`);
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        setTimeAgo(`${minutes} minute${minutes !== 1 ? 's' : ''} ago`);
      } else {
        setTimeAgo(lastRefreshed.toLocaleTimeString());
      }
    };
    
    updateTimeAgo();
    const interval = setInterval(updateTimeAgo, 1000);
    
    return () => clearInterval(interval);
  }, [lastRefreshed]);
  
  return (
    <div className="flex items-center space-x-2">
      {isLoading ? (
        <motion.div
          animate={{ scale: [1, 1.05, 1], opacity: [0.8, 1, 0.8] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="w-2 h-2 rounded-full bg-blue-500"
        />
      ) : (
        <div className="w-2 h-2 rounded-full bg-green-400" />
      )}
      <span className="text-sm text-gray-500">
        {isLoading ? 'Refreshing...' : `Last updated: ${timeAgo}`}
      </span>
      {!isLoading && (
        <button 
          onClick={onRefresh}
          className="text-primary-600 hover:text-primary-800 text-sm"
          aria-label="Refresh data"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-4 w-4" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
            />
          </svg>
        </button>
      )}
    </div>
  );
};

export default RefreshIndicator; 