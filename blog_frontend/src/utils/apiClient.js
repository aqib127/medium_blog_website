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

// Helper to safely parse JSON responses
const safeParseJSON = async (response) => {
  const text = await response.text();
  if (!text) {
    return {};
  }
  try {
    return JSON.parse(text);
  } catch {
    // If it's not JSON, return the text as an error message
    throw new Error(`Server error: ${response.status} - ${text.substring(0, 100)}`);
  }
};

// Helper to handle non-JSON responses gracefully
const handleResponse = async (response) => {
  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}`;
    try {
      const errorData = await safeParseJSON(response);
      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (typeof errorData === 'object' && errorData.message) {
        errorMessage = errorData.message;
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      }
    } catch {
      // If we can't parse the error, use the status text
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  return safeParseJSON(response);
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
            return handleResponse(retryRes);
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
                  resolve(handleResponse(retryRes));
                } catch (err) {
                  reject(err);
                }
              },
              reject,
            });
          });
        }
      }

      // For non-401 responses, handle normally
      return handleResponse(response);
    } catch (error) {
      // Network errors or other fetch errors
      console.error('API Client Error:', error);
      throw new Error(error.message || 'Network error occurred');
    }
  };

  return makeRequest();
};

export default apiClient;