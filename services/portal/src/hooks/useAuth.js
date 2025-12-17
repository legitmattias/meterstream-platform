import { useState, useEffect } from 'react';
import { api } from '../lib/api';

/**
 * Manage authnetication state and provide login, logout, and isAuthenticated functions.
 * Saves tokens in sessionStorage.
 * Calls API, stores token, decodes JWT, clears token on logout
 * @returns 
 */
export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const access_token = sessionStorage.getItem('access_token');
      if (access_token) {
        api.setToken(access_token);
        setUser({ access_token });
      }
      setLoading(false);
    };
    
    initAuth();
  }, []);

  const login = async (email, password) => {
    const data = await api.login(email, password);
    sessionStorage.setItem('access_token', data.access_token);
    setUser({ email, access_token: data.access_token });
    return data;
  };

  const logout = () => {
    api.clearToken();
    sessionStorage.removeItem('access_token');
    setUser(null);
  };

  const isAuthenticated = () => {
    return !!user;
  };

  return {
    user,
    loading,
    login,
    logout,
    isAuthenticated,
  };
}
