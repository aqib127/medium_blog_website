const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1/';

export const endpoints = {
  register: `${baseURL}auth/register/`,
  login: `${baseURL}auth/login/`,
  refresh: `${baseURL}auth/refresh/`,
  verify: `${baseURL}auth/verify/`,
  me: `${baseURL}auth/me/`,

  users: (handle) => `${baseURL}users/${handle}/`,
  userStories: (handle) => `${baseURL}users/${handle}/stories/`,
  userFollowers: (handle) => `${baseURL}users/${handle}/followers/`,
  userFollowing: (handle) => `${baseURL}users/${handle}/following/`,
  userFollow: (handle) => `${baseURL}users/${handle}/follow/`,
  userUpdate: (handle) => `${baseURL}users/${handle}/update/`,
  userAvatar: (handle) => `${baseURL}users/${handle}/avatar/`,

  articles: `${baseURL}articles/`,
  article: (id) => `${baseURL}articles/${id}/`,
  clap: (id) => `${baseURL}articles/${id}/clap/`,
  featured: `${baseURL}articles/featured/`,
  trending: `${baseURL}articles/trending/`,

  comments: `${baseURL}comments/`,
  commentList: (articleId) => `${baseURL}comments/?article=${articleId}`,

  bookmarks: `${baseURL}bookmarks/`,
  bookmark: (articleId) => `${baseURL}bookmarks/${articleId}/`,

  notifications: `${baseURL}notifications/`,
  notificationRead: (id) => `${baseURL}notifications/${id}/read/`,
  notificationReadAll: `${baseURL}notifications/read_all/`,

  history: `${baseURL}history/`,
  reports: `${baseURL}reports/`,

  tags: `${baseURL}articles/tags/`,
  tagArticles: (slug) => `${baseURL}articles/?tags=${slug}`,
};