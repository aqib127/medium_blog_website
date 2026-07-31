import { endpoints } from '../config/api';

const apiClient = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access');
  
  // Build headers – start with provided headers
  const headers = { ...options.headers };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  // Set Content-Type only if not FormData and not already set
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(endpoint, {
      ...options,
      headers,
    });

    // If token expired, try refresh
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
            localStorage.removeItem('access');
            localStorage.removeItem('refresh');
            localStorage.removeItem('user');
            window.location.href = '/signin';
            return response;
          }
        } catch {
          return response;
        }
      }
    }
    return response;
  } catch (error) {
    console.error('apiClient fetch error:', error);
    throw error;
  }
};

export default apiClient;