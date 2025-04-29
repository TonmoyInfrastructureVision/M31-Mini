import axios, { AxiosError, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: unknown): Promise<unknown> => {
    return Promise.reject(error);
  }
);

// Add a response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => {
    return response;
  },
  (error: unknown): Promise<unknown> => {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      const response = axiosError.response;
      
      // Handle error responses
      if (response && response.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export type ApiResponse<T> = {
  data: T;
  error?: string;
  status: number;
};

export const apiRequest = async <T>(
  config: AxiosRequestConfig
): Promise<ApiResponse<T>> => {
  try {
    const response: AxiosResponse<T> = await apiClient(config);
    return {
      data: response.data,
      status: response.status,
    };
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      const errorResponse = axiosError.response;
      
      if (errorResponse && errorResponse.data) {
        return {
          data: {} as T,
          error: (errorResponse.data as any).detail || 'An error occurred',
          status: errorResponse.status,
        };
      }
    }
    return {
      data: {} as T,
      error: 'Network error',
      status: 500,
    };
  }
};

export default apiClient; 