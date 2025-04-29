import { useState, useCallback } from 'react';
import { ApiErrorResponse } from '../utils/errors';

export interface FormErrors {
  [key: string]: string;
}

export interface UseFormErrorReturn {
  formErrors: FormErrors;
  globalError: string | null;
  setFormError: (field: string, message: string) => void;
  setGlobalError: (message: string | null) => void;
  handleApiError: (error: ApiErrorResponse) => void;
  clearErrors: () => void;
}

export const useFormError = (): UseFormErrorReturn => {
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [globalError, setGlobalError] = useState<string | null>(null);

  const setFormError = useCallback((field: string, message: string): void => {
    setFormErrors(prev => ({
      ...prev,
      [field]: message
    }));
  }, []);

  const clearErrors = useCallback((): void => {
    setFormErrors({});
    setGlobalError(null);
  }, []);

  const handleApiError = useCallback((error: ApiErrorResponse): void => {
    if (error.details && Object.keys(error.details).length > 0) {
      const formattedErrors: FormErrors = {};
      
      Object.entries(error.details).forEach(([field, messages]) => {
        formattedErrors[field] = Array.isArray(messages) && messages.length > 0 
          ? messages[0] 
          : 'Invalid value';
      });
      
      setFormErrors(formattedErrors);
    } else {
      setGlobalError(error.message || 'An error occurred');
    }
  }, []);

  return {
    formErrors,
    globalError,
    setFormError,
    setGlobalError,
    handleApiError,
    clearErrors
  };
}; 