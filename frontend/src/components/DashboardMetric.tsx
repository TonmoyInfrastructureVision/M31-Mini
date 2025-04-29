import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface DashboardMetricProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: number;
  footer?: ReactNode;
  icon?: ReactNode;
}

const DashboardMetric = ({
  title,
  value,
  subtitle,
  change,
  footer,
  icon
}: DashboardMetricProps): React.ReactElement => {
  const isPositiveChange = change !== undefined && change > 0;
  const isNegativeChange = change !== undefined && change < 0;
  
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {icon && (
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-primary-100 text-primary-600">
                {icon}
              </div>
            )}
          </div>
          <div className={icon ? "ml-5 w-0 flex-1" : "w-full"}>
            <dt className="text-sm font-medium text-gray-500 truncate">
              {title}
            </dt>
            <div className="flex items-baseline">
              <motion.div 
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-2xl font-semibold text-gray-900"
              >
                {value}
              </motion.div>
              
              {change !== undefined && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 }}
                  className={`ml-2 flex items-baseline text-sm font-semibold ${
                    isPositiveChange 
                      ? 'text-green-600' 
                      : isNegativeChange 
                        ? 'text-red-600' 
                        : 'text-gray-500'
                  }`}
                >
                  {isPositiveChange && (
                    <svg className="self-center flex-shrink-0 h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                  
                  {isNegativeChange && (
                    <svg className="self-center flex-shrink-0 h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                  
                  <span className="sr-only">
                    {isPositiveChange ? 'Increased by' : isNegativeChange ? 'Decreased by' : 'Changed by'}
                  </span>
                  {Math.abs(change)}%
                </motion.div>
              )}
            </div>
            
            {subtitle && (
              <dd className="mt-1 text-sm text-gray-500">
                {subtitle}
              </dd>
            )}
          </div>
        </div>
      </div>
      
      {footer && (
        <div className="bg-gray-50 px-5 py-3">
          {footer}
        </div>
      )}
    </div>
  );
};

export default DashboardMetric; 