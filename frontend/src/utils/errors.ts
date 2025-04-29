import { AxiosError } from 'axios';

export type ApiErrorType = 'auth' | 'network' | 'validation' | 'server' | 'notfound' | 'unknown';

export interface ApiErrorResponse {
  type: ApiErrorType;
  message: string;
  status?: number;
  details?: Record<string, string[]>;
}

interface ErrorResponseData {
  message?: string;
  errors?: Record<string, string[]>;
}

export const parseApiError = (error: unknown): ApiErrorResponse => {
  if (!error) {
    return {
      type: 'unknown',
      message: 'An unknown error occurred',
    };
  }

  if (typeof window === 'undefined' || !window.navigator.onLine) {
    return {
      type: 'network',
      message: 'Network connection lost',
    };
  }

  if (isAxiosError(error)) {
    const status = error.response?.status || 500;
    const responseData = error.response?.data as ErrorResponseData | undefined;
    
    if (status === 401 || status === 403) {
      return {
        type: 'auth',
        message: 'Authentication error',
        status,
      };
    }
    
    if (status === 404) {
      return {
        type: 'notfound',
        message: 'Resource not found',
        status,
      };
    }
    
    if (status === 422) {
      return {
        type: 'validation',
        message: 'Validation error',
        status,
        details: responseData?.errors,
      };
    }
    
    if (status >= 500) {
      return {
        type: 'server',
        message: 'Server error',
        status,
      };
    }
    
    return {
      type: 'unknown',
      message: responseData?.message || error.message || 'Unknown error',
      status,
    };
  }
  
  return {
    type: 'unknown',
    message: error instanceof Error ? error.message : 'Unknown error occurred',
  };
};

export const isAxiosError = (error: unknown): error is AxiosError => {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    (error as AxiosError).isAxiosError === true
  );
}; 