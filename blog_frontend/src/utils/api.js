import apiClient from './apiClient';
import { endpoints } from '../config/api';

// Fetch a single article by ID (or slug)
export const getArticleBySlug = async (id) => {
  try {
    const res = await apiClient(endpoints.article(id));
    if (!res.ok) throw new Error('Failed to fetch article');
    return await res.json();
  } catch (err) {
    console.error('Error fetching article:', err);
    throw err;
  }
};

// Fetch all articles (with optional filters)
export const getArticles = async (params = {}) => {
  const query = new URLSearchParams(params).toString();
  const url = query ? `${endpoints.articles}?${query}` : endpoints.articles;
  
  try {
    const res = await apiClient(url);
    if (!res.ok) throw new Error('Failed to fetch articles');
    const data = await res.json();
    return data.results || data;
  } catch (err) {
    console.error('Error fetching articles:', err);
    throw err;
  }
};

// Fetch articles by tag slug
export const getArticlesByTag = async (slug) => {
  return getArticles({ tags__slug: slug });
};