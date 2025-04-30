import React, { ReactNode, ButtonHTMLAttributes } from 'react';
import clsx from 'clsx';
import { motion } from 'framer-motion';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  rounded?: 'md' | 'full' | 'none';
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  rounded = 'md',
  className,
  disabled,
  ...props
}: ButtonProps): React.ReactElement {
  const baseClasses = 'inline-flex items-center justify-center font-medium transition-all duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 active:translate-y-px';
  
  const variantClasses = {
    primary: 'text-white bg-indigo-600 hover:bg-indigo-700 focus-visible:ring-indigo-500 border border-transparent shadow-sm',
    secondary: 'text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus-visible:ring-indigo-500 border border-transparent',
    outline: 'text-slate-700 bg-white hover:bg-slate-50 focus-visible:ring-indigo-500 border border-slate-300 shadow-sm',
    ghost: 'text-slate-700 bg-transparent hover:bg-slate-100 focus-visible:ring-indigo-500 border border-transparent',
    danger: 'text-white bg-red-600 hover:bg-red-700 focus-visible:ring-red-500 border border-transparent shadow-sm',
    success: 'text-white bg-emerald-600 hover:bg-emerald-700 focus-visible:ring-emerald-500 border border-transparent shadow-sm'
  };
  
  const sizeClasses = {
    xs: 'px-2.5 py-1.5 text-xs',
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  };
  
  const roundedClasses = {
    none: 'rounded-none',
    md: 'rounded-md',
    full: 'rounded-full',
  };
  
  const widthClass = fullWidth ? 'w-full' : '';
  const disabledClass = disabled || isLoading ? 'opacity-60 cursor-not-allowed' : '';
  
  const spinnerVariants = {
    loading: {
      rotate: 360,
      transition: {
        repeat: Infinity,
        duration: 1,
        ease: "linear"
      }
    }
  };
  
  return (
    <button
      type="button"
      disabled={disabled || isLoading}
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        roundedClasses[rounded],
        widthClass,
        disabledClass,
        className
      )}
      {...props}
    >
      {isLoading && (
        <motion.svg 
          className="-ml-1 mr-2 h-4 w-4" 
          viewBox="0 0 24 24"
          variants={spinnerVariants}
          animate="loading"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </motion.svg>
      )}
      
      {icon && iconPosition === 'left' && !isLoading && (
        <span className="mr-2 -ml-0.5">{icon}</span>
      )}
      
      {children}
      
      {icon && iconPosition === 'right' && (
        <span className="ml-2 -mr-0.5">{icon}</span>
      )}
    </button>
  );
} 