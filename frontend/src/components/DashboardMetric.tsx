import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';
import * as Tooltip from '@radix-ui/react-tooltip';

interface DashboardMetricProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: number;
  footer?: ReactNode;
  icon?: ReactNode;
  color?: 'blue' | 'indigo' | 'purple' | 'green' | 'red' | 'orange';
}

const DashboardMetric = ({
  title,
  value,
  subtitle,
  change,
  footer,
  icon,
  color = 'indigo'
}: DashboardMetricProps): React.ReactElement => {
  const isPositiveChange = change !== undefined && change > 0;
  const isNegativeChange = change !== undefined && change < 0;
  
  const getColorClasses = (colorName: string): { bg: string, text: string, bgLight: string } => {
    switch (colorName) {
      case 'blue':
        return { bg: 'bg-blue-600', text: 'text-blue-600', bgLight: 'bg-blue-50' };
      case 'indigo':
        return { bg: 'bg-indigo-600', text: 'text-indigo-600', bgLight: 'bg-indigo-50' };
      case 'purple':
        return { bg: 'bg-purple-600', text: 'text-purple-600', bgLight: 'bg-purple-50' };
      case 'green':
        return { bg: 'bg-emerald-600', text: 'text-emerald-600', bgLight: 'bg-emerald-50' };
      case 'red':
        return { bg: 'bg-red-600', text: 'text-red-600', bgLight: 'bg-red-50' };
      case 'orange':
        return { bg: 'bg-orange-600', text: 'text-orange-600', bgLight: 'bg-orange-50' };
      default:
        return { bg: 'bg-indigo-600', text: 'text-indigo-600', bgLight: 'bg-indigo-50' };
    }
  };
  
  const colorClasses = getColorClasses(color);
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-100 hover:shadow-md transition-shadow duration-200"
    >
      <div className="p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {icon && (
              <div className={`flex items-center justify-center h-12 w-12 rounded-lg ${colorClasses.bgLight} ${colorClasses.text}`}>
                {icon}
              </div>
            )}
          </div>
          <div className={icon ? "ml-5 w-0 flex-1" : "w-full"}>
            <dt className="text-sm font-medium text-slate-500 truncate">
              {title}
            </dt>
            <div className="flex items-baseline">
              <motion.div 
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-3xl font-bold text-slate-900"
              >
                {value}
              </motion.div>
              
              {change !== undefined && (
                <Tooltip.Provider>
                  <Tooltip.Root>
                    <Tooltip.Trigger asChild>
                      <motion.div 
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 }}
                        className={`ml-2 flex items-baseline text-sm font-semibold cursor-help px-2 py-0.5 rounded-full ${
                          isPositiveChange 
                            ? 'text-emerald-700 bg-emerald-50' 
                            : isNegativeChange 
                              ? 'text-red-700 bg-red-50' 
                              : 'text-slate-700 bg-slate-100'
                        }`}
                      >
                        {isPositiveChange && (
                          <svg className="self-center flex-shrink-0 h-3.5 w-3.5 mr-1" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                            <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                        
                        {isNegativeChange && (
                          <svg className="self-center flex-shrink-0 h-3.5 w-3.5 mr-1" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                            <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                        
                        <span className="sr-only">
                          {isPositiveChange ? 'Increased by' : isNegativeChange ? 'Decreased by' : 'Changed by'}
                        </span>
                        {Math.abs(change)}%
                      </motion.div>
                    </Tooltip.Trigger>
                    <Tooltip.Portal>
                      <Tooltip.Content className="bg-slate-900 text-white px-3 py-1 rounded text-xs" sideOffset={5}>
                        {isPositiveChange 
                          ? `Increased by ${Math.abs(change)}%` 
                          : isNegativeChange 
                            ? `Decreased by ${Math.abs(change)}%` 
                            : `Changed by ${Math.abs(change)}%`
                        }
                        <Tooltip.Arrow className="fill-slate-900" />
                      </Tooltip.Content>
                    </Tooltip.Portal>
                  </Tooltip.Root>
                </Tooltip.Provider>
              )}
            </div>
            
            {subtitle && (
              <dd className="mt-2 text-sm text-slate-500">
                {subtitle}
              </dd>
            )}
          </div>
        </div>
      </div>
      
      {footer && (
        <div className="bg-slate-50 px-6 py-3 border-t border-slate-100">
          {footer}
        </div>
      )}
    </motion.div>
  );
};

export default DashboardMetric; 