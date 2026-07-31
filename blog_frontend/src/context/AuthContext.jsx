import { createContext, useContext, useEffect, useState } from 'react';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access');
    if (token) {
      fetchMe()
        .then((u) => {
          setUser(u);
          localStorage.setItem('user', JSON.stringify(u));
        })
        .catch(() => {
          localStorage.removeItem('access');
          localStorage.removeItem('refresh');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const fetchMe = async () => {
    const res = await apiClient(endpoints.me);
    if (!res.ok) throw new Error('Failed to fetch user');
    return res.json();
  };

  const signIn = async (email, password) => {
    try {
      const res = await fetch(endpoints.login, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        // Extract meaningful error message
        let errorMsg = data.detail || data.message || 'Invalid credentials.';
        if (data.non_field_errors) errorMsg = data.non_field_errors.join(' ');
        return { success: false, error: errorMsg };
      }
      localStorage.setItem('access', data.access);
      localStorage.setItem('refresh', data.refresh);
      setUser(data.user);
      localStorage.setItem('user', JSON.stringify(data.user));
      return { success: true, user: data.user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const signUp = async (email, name, password, handle = '') => {
    try {
      const res = await fetch(endpoints.register, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, password, handle }),
      });
      const data = await res.json();
      if (!res.ok) {
        // Build error message from field errors
        let errorMsg = 'Registration failed.';
        if (data.email) errorMsg = data.email.join(' ');
        else if (data.password) errorMsg = data.password.join(' ');
        else if (data.name) errorMsg = data.name.join(' ');
        else if (data.handle) errorMsg = data.handle.join(' ');
        else if (data.detail) errorMsg = data.detail;
        else if (data.non_field_errors) errorMsg = data.non_field_errors.join(' ');
        return { success: false, error: errorMsg };
      }
      // Auto-login after registration
      return await signIn(email, password);
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const signOut = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('user');
    setUser(null);
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);