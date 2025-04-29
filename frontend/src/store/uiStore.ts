import { create } from 'zustand';

interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}

interface UIState {
  isSidebarOpen: boolean;
  isDarkMode: boolean;
  toastMessages: ToastMessage[];
  toggleSidebar: () => void;
  toggleDarkMode: () => void;
  addToast: (toast: Omit<ToastMessage, 'id'>) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  isSidebarOpen: true,
  isDarkMode: false,
  toastMessages: [],

  toggleSidebar: (): void => {
    set(state => ({ isSidebarOpen: !state.isSidebarOpen }));
  },

  toggleDarkMode: (): void => {
    set(state => {
      const newDarkMode = !state.isDarkMode;
      
      if (typeof window !== 'undefined') {
        if (newDarkMode) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
        localStorage.setItem('darkMode', String(newDarkMode));
      }
      
      return { isDarkMode: newDarkMode };
    });
  },

  addToast: (toast: Omit<ToastMessage, 'id'>): string => {
    const id = Date.now().toString();
    
    set(state => ({
      toastMessages: [...state.toastMessages, { ...toast, id }]
    }));
    
    if (toast.duration !== 0) {
      const duration = toast.duration || 5000;
      setTimeout(() => {
        get().removeToast(id);
      }, duration);
    }
    
    return id;
  },

  removeToast: (id: string): void => {
    set(state => ({
      toastMessages: state.toastMessages.filter(toast => toast.id !== id)
    }));
  },

  clearToasts: (): void => {
    set({ toastMessages: [] });
  }
})); 