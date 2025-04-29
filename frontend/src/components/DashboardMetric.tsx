import React, { ReactNode } from 'react';

interface DashboardMetricProps {
  title: string;
  value: string | number;
  footer?: ReactNode;
  className?: string;
}

export default function DashboardMetric({ 
  title, 
  value, 
  footer, 
  className = ''
}: DashboardMetricProps): React.ReactElement {
  return (
    <div className={`bg-white overflow-hidden shadow rounded-lg ${className}`}>
      <div className="px-4 py-5 sm:p-6">
        <dl>
          <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
          <dd className="mt-1 text-3xl font-semibold text-gray-900">{value}</dd>
        </dl>
      </div>
      {footer && (
        <div className="bg-gray-50 px-4 py-4 sm:px-6">
          {footer}
        </div>
      )}
    </div>
  );
} 