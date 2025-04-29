export const isValidName = (name: string): boolean => {
  if (!name) return false;
  return name.trim().length >= 3;
};

export const isValidEmail = (email: string): boolean => {
  if (!email) return false;
  
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailRegex.test(email);
};

export const isValidUrl = (url: string): boolean => {
  if (!url) return false;
  
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const isValidFilePath = (path: string): boolean => {
  if (!path) return true;
  
  const pathRegex = /^[a-zA-Z0-9_\-./]+$/;
  return pathRegex.test(path);
}; 