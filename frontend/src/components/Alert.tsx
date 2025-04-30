import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

type AlertVariant = 'info' | 'success' | 'warning' | 'error';

interface AlertProps {
  title?: string;
  children: ReactNode;
  variant?: AlertVariant;
  icon?: ReactNode;
  dismissible?: boolean;
  onDismiss?: () => void;
}

const Alert = ({
  title,
  children,
  variant = 'info',
  icon,
  dismissible = false,
  onDismiss,
}: AlertProps): React.ReactElement => {
  const getVariantStyles = (): { 
    container: string; 
    icon: string; 
    title: string; 
    content: string;
    closeButton: string;
  } => {
    switch (variant) {
      case 'info':
        return {
          container: 'bg-blue-50 border-blue-200',
          icon: 'text-blue-500',
          title: 'text-blue-800',
          content: 'text-blue-700',
          closeButton: 'text-blue-500 hover:bg-blue-100',
        };
      case 'success':
        return {
          container: 'bg-emerald-50 border-emerald-200',
          icon: 'text-emerald-500',
          title: 'text-emerald-800',
          content: 'text-emerald-700',
          closeButton: 'text-emerald-500 hover:bg-emerald-100',
        };
      case 'warning':
        return {
          container: 'bg-amber-50 border-amber-200',
          icon: 'text-amber-500',
          title: 'text-amber-800',
          content: 'text-amber-700',
          closeButton: 'text-amber-500 hover:bg-amber-100',
        };
      case 'error':
        return {
          container: 'bg-red-50 border-red-200',
          icon: 'text-red-500',
          title: 'text-red-800',
          content: 'text-red-700',
          closeButton: 'text-red-500 hover:bg-red-100',
        };
      default:
        return {
          container: 'bg-blue-50 border-blue-200',
          icon: 'text-blue-500',
          title: 'text-blue-800',
          content: 'text-blue-700',
          closeButton: 'text-blue-500 hover:bg-blue-100',
        };
    }
  };

  const styles = getVariantStyles();

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={clsx(
        'rounded-lg border p-4 flex',
        styles.container
      )}
    >
      {icon && (
        <div className={clsx('flex-shrink-0 mr-3', styles.icon)}>
          {icon}
        </div>
      )}
      
      <div className="flex-1">
        {title && (
          <h3 className={clsx('text-sm font-medium mb-1', styles.title)}>
            {title}
          </h3>
        )}
        <div className={clsx('text-sm', styles.content)}>
          {children}
        </div>
      </div>
      
      {dismissible && onDismiss && (
        <div className="ml-3 flex-shrink-0">
          <button
            type="button"
            className={clsx('inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500', styles.closeButton)}
            onClick={onDismiss}
          >
            <span className="sr-only">Dismiss</span>
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default Alert; 