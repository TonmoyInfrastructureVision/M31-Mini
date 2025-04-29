interface AuthToken {
  token: string;
  expiresAt: number;
}

const TOKEN_KEY = 'auth_token';

export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  const tokenData = localStorage.getItem(TOKEN_KEY);
  if (!tokenData) return null;
  
  try {
    const parsedData: AuthToken = JSON.parse(tokenData);
    
    if (Date.now() > parsedData.expiresAt) {
      localStorage.removeItem(TOKEN_KEY);
      return null;
    }
    
    return parsedData.token;
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    return null;
  }
};

export const setToken = (token: string, expiresInSeconds: number = 3600): void => {
  if (typeof window === 'undefined') return;
  
  const tokenData: AuthToken = {
    token,
    expiresAt: Date.now() + expiresInSeconds * 1000
  };
  
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokenData));
};

export const removeToken = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
};

export const isAuthenticated = (): boolean => {
  return getToken() !== null;
}; 