import { endpoints } from '../config/api';

// Prevent multiple refresh requests at the same time
let isRefreshing = false;
let refreshSubscribers = [];

const subscribeTokenRefresh = (cb) => {
  refreshSubscribers.push(cb);
};

const onTokenRefreshed = () => {
  refreshSubscribers.forEach((cb) => cb());
  refreshSubscribers = [];
};

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

          if (refreshRes.ok) {
            const data = await refreshRes.json();
            localStorage.setItem('access', data.access);
            token = data.access;
            // Update headers with new token
            headers['Authorization'] = `Bearer ${data.access}`;
            isRefreshing = false;
            onTokenRefreshed();
            // Retry the original request with new token
            const retryRes = await fetch(endpoint, {
              ...options,
              headers,
            });
            return retryRes;
          } else {
            // Refresh failed – clear tokens and throw error
            localStorage.removeItem('access');
            localStorage.removeItem('refresh');
            localStorage.removeItem('user');
            isRefreshing = false;
            throw new Error('Session expired. Please sign in again.');
          }
        } catch (error) {
          localStorage.removeItem('access');
          localStorage.removeItem('refresh');
          localStorage.removeItem('user');
          isRefreshing = false;
          throw new Error('Session expired. Please sign in again.');
        }
      } else {
        // Another request is already refreshing – wait for it
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh(async () => {
            try {
              const newToken = localStorage.getItem('access');
              if (!newToken) {
                reject(new Error('Session expired.'));
                return;
              }
              headers['Authorization'] = `Bearer ${newToken}`;
              const retryRes = await fetch(endpoint, {
                ...options,
                headers,
              });
              resolve(retryRes);
            } catch (err) {
              reject(err);
            }
          });
        });
      }
    }

    return response;
  };

  return makeRequest();
};

// CRITICAL LINE: This must be here!
export default apiClient;