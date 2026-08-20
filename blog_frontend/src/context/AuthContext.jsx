import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';

const AuthContext = createContext(null);

// DRF returns field errors as `{ field: [messages] }`. Walk that shape
// generically so sign-in and sign-up report every field error consistently.
const extractErrors = (data) => {
  if (!data || typeof data !== 'object') return 'Something went wrong.';
  const messages = [];
  Object.values(data).forEach((value) => {
    if (Array.isArray(value)) {
      value.forEach((m) => {
        if (typeof m === 'string') messages.push(m);
        else if (m && typeof m === 'object') messages.push(extractErrors(m));
      });
    } else if (typeof value === 'string') {
      messages.push(value);
    }
  });
  return messages.join(' ') || 'Something went wrong.';
};

// Guard against a non-JSON body (e.g. an HTML error page from a proxy).
const parseJson = async (res) => {
  try {
    return await res.json();
  } catch {
    return {};
  }
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const token = localStorage.getItem('access');
    if (token) {
      fetchMe()
        .then((u) => {
          if (!active) return;
          setUser(u);
          localStorage.setItem('user', JSON.stringify(u));
        })
        .catch(() => {
          localStorage.removeItem('access');
          localStorage.removeItem('refresh');
          localStorage.removeItem('user');
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    } else {
      setLoading(false);
    }
    return () => {
      active = false;
    };
  }, []);

  const fetchMe = async () => {
    const res = await apiClient(endpoints.me);
    if (!res.ok) {
      throw new Error('Failed to fetch user');
    }
    return res.json();
  };

  const storeAuth = (data) => {
    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    setUser(data.user);
    localStorage.setItem('user', JSON.stringify(data.user));
  };

  const signIn = async (email, password) => {
    try {
      const res = await fetch(endpoints.login, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await parseJson(res);
      if (!res.ok) {
        return { success: false, error: extractErrors(data) };
      }
      storeAuth(data);
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
      const data = await parseJson(res);
      if (!res.ok) {
        return { success: false, error: extractErrors(data) };
      }
      // The register response already includes tokens + user — no second login.
      storeAuth(data);
      return { success: true, user: data.user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const signOut = () => {
    const refresh = localStorage.getItem('refresh');
    // Best-effort server-side blacklist; local state is cleared regardless.
    if (refresh) {
      fetch(endpoints.logout, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      }).catch(() => {});
    }
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('user');
    setUser(null);
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  const value = useMemo(
    () => ({ user, loading, signIn, signUp, signOut, updateUser }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
