import { endpoints } from '../config/api';

// Prevent multiple refresh requests at the same time
let isRefreshing = false;
let refreshSubscribers = [];

const subscribeTokenRefresh = (cb) => {
  refreshSubscribers.push(cb);
};

const onTokenRefreshed = (newToken) => {
  refreshSubscribers.forEach((cb) => cb.resolve(newToken));
  refreshSubscribers = [];
};

const onTokenRefreshFailed = (error) => {
  refreshSubscribers.forEach((cb) => cb.reject(error));
  refreshSubscribers = [];
};

/**
 * apiClient — fetch-like wrapper with automatic JWT refresh.
 *
 * Returns the raw `Response` object (like `fetch`), so callers can use
 * `res.ok`, `res.status`, `res.json()`, etc.
 */
const apiClient = async (endpoint, options = {}) => {
  // Get token from localStorage
  let token = localStorage.getItem('access');
  const refresh = localStorage.getItem('refresh');

  const headers = { ...options.headers };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const makeRequest = async () => {
    try {
      const response = await fetch(endpoint, {
        ...options,
        headers,
      });

      // If 401 and we have a refresh token, attempt to refresh
      if (response.status === 401 && refresh) {
        if (!isRefreshing) {
          isRefreshing = true;
          try {
            const refreshRes = await fetch(endpoints.refresh, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh }),
            });

            if (!refreshRes.ok) {
              throw new Error('Session expired. Please sign in again.');
            }

            const data = await refreshRes.json();
            localStorage.setItem('access', data.access);
            token = data.access;
            headers['Authorization'] = `Bearer ${data.access}`;
            onTokenRefreshed(data.access);

            // Retry the original request with the new token
            const retryRes = await fetch(endpoint, {
              ...options,
              headers,
            });
            return retryRes;   // ← Return raw Response
          } catch (error) {
            localStorage.removeItem('access');
            localStorage.removeItem('refresh');
            localStorage.removeItem('user');
            onTokenRefreshFailed(error);
            throw error;
          } finally {
            isRefreshing = false;
          }
        } else {
          // Another request is already refreshing – wait for it
          return new Promise((resolve, reject) => {
            subscribeTokenRefresh({
              resolve: async (newToken) => {
                try {
                  headers['Authorization'] = `Bearer ${newToken}`;
                  const retryRes = await fetch(endpoint, {
                    ...options,
                    headers,
                  });
                  resolve(retryRes);   // ← Return raw Response
                } catch (err) {
                  reject(err);
                }
              },
              reject,
            });
          });
        }
      }

      // For non-401 responses, return the raw Response
      return response;   // ← Return raw Response
    } catch (error) {
      console.error('API Client Error:', error);
      throw new Error(error.message || 'Network error occurred');
    }
  };

  return makeRequest();
};

export default apiClient;