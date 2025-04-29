import { logger } from './logger';

export const getItem = <T>(key: string, defaultValue: T): T => {
  if (typeof window === 'undefined') return defaultValue;
  
  try {
    const item = window.localStorage.getItem(key);
    
    if (item === null) {
      return defaultValue;
    }
    
    return JSON.parse(item) as T;
  } catch {
    return defaultValue;
  }
};

export const setItem = <T>(key: string, value: T): void => {
  if (typeof window === 'undefined') return;
  
  try {
    const serializedValue = JSON.stringify(value);
    window.localStorage.setItem(key, serializedValue);
  } catch (err) {
    logger.error('Error saving to localStorage:', err);
  }
};

export const removeItem = (key: string): void => {
  if (typeof window === 'undefined') return;
  
  window.localStorage.removeItem(key);
};

export const clear = (): void => {
  if (typeof window === 'undefined') return;
  
  window.localStorage.clear();
}; 