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

const apiClient = async (endpoint, options = {}) => {
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

            const retryRes = await fetch(endpoint, {
              ...options,
              headers,
            });
            return retryRes;
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
          return new Promise((resolve, reject) => {
            subscribeTokenRefresh({
              resolve: async (newToken) => {
                try {
                  headers['Authorization'] = `Bearer ${newToken}`;
                  const retryRes = await fetch(endpoint, {
                    ...options,
                    headers,
                  });
                  resolve(retryRes);
                } catch (err) {
                  reject(err);
                }
              },
              reject,
            });
          });
        }
      }

      return response;
    } catch (error) {
      console.error('API Client Error:', error);
      throw new Error(error.message || 'Network error occurred');
    }
  };

  return makeRequest();
};

export default apiClient;
