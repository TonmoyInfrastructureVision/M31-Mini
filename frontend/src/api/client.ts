import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    const response = error.response;
    
    // Handle error responses
    if (response && response.status === 401) {
      // Handle unauthorized
      console.error('Unauthorized access');
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
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      return {
        data: {} as T,
        error: error.response.data.detail || 'An error occurred',
        status: error.response.status,
      };
    }
    return {
      data: {} as T,
      error: 'Network error',
      status: 500,
    };
  }
};

export default apiClient; 