const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1/';

const normalizedBase = baseURL.endsWith('/') ? baseURL : baseURL + '/';

export const endpoints = {

  register: `${normalizedBase}auth/register/`,
  login: `${normalizedBase}auth/login/`,
  refresh: `${normalizedBase}auth/refresh/`,
  verify: `${normalizedBase}auth/verify/`,
  me: `${normalizedBase}auth/me/`,
  logout: `${normalizedBase}auth/logout/`,

  // Users
  users: (handle) => `${normalizedBase}users/${handle}/`,
  userStories: (handle) => `${normalizedBase}users/${handle}/stories/`,
  userFollowers: (handle) => `${normalizedBase}users/${handle}/followers/`,
  userFollowing: (handle) => `${normalizedBase}users/${handle}/following/`,
  userFollow: (handle) => `${normalizedBase}users/${handle}/follow/`,
  userUpdate: (handle) => `${normalizedBase}users/${handle}/update/`,
  userAvatar: (handle) => `${normalizedBase}users/${handle}/avatar/`,

  // Articles
  articles: `${normalizedBase}articles/`,
  article: (id) => `${normalizedBase}articles/${id}/`,
  clap: (id) => `${normalizedBase}articles/${id}/clap/`,
  featured: `${normalizedBase}articles/featured/`,
  trending: `${normalizedBase}articles/trending/`,

  // Comments
  comments: `${normalizedBase}comments/`,
  commentList: (articleId) => `${normalizedBase}comments/?article=${articleId}`,

  // Bookmarks
  bookmarks: `${normalizedBase}bookmarks/`,
  bookmark: (articleId) => `${normalizedBase}bookmarks/${articleId}/`,

  // Notifications
  notifications: `${normalizedBase}notifications/`,
  notificationRead: (id) => `${normalizedBase}notifications/${id}/read/`,
  notificationReadAll: `${normalizedBase}notifications/read_all/`,

  // History & Reports
  history: `${normalizedBase}history/`,
  reports: `${normalizedBase}reports/`,

  // Tags
  tags: `${normalizedBase}articles/tags/`,
  tagArticles: (slug) => `${normalizedBase}articles/?tags__slug=${slug}`,

  // ✅ CHATBOT FIXED: Points to the correct Django endpoint
  chatbot: `${normalizedBase}rag/chat/stream/`,
};