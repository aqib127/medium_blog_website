import { endpoints } from '../config/api';

const apiClient = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access');
  const headers = { ...options.headers };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  // If token expired, attempt refresh
  if (response.status === 401) {
    const refresh = localStorage.getItem('refresh');
    if (refresh) {
      try {
        const refreshRes = await fetch(endpoints.refresh, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh }),
        });
        if (refreshRes.ok) {
          const data = await refreshRes.json();
          localStorage.setItem('access', data.access);
          // Retry original request with new token
          const retry = await fetch(endpoint, {
            ...options,
            headers: {
              ...headers,
              'Authorization': `Bearer ${data.access}`,
            },
          });
          return retry;
        } else {
          // Refresh failed – clear tokens and throw error (will be caught by component)
          localStorage.removeItem('access');
          localStorage.removeItem('refresh');
          localStorage.removeItem('user');
          throw new Error('Session expired. Please sign in again.');
        }
      } catch (refreshError) {
        // If refresh network error, still throw so component can handle
        throw refreshError;
      }
    } else {
      // No refresh token – throw so component can handle
      throw new Error('No refresh token. Please sign in.');
    }
  }

  return response;
};

export default apiClient;