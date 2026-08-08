import { useEffect, useState } from 'react';
import ArticleCard from '../components/ArticleCard';
import Sidebar from '../components/Sidebar';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';

/**
 * FIX: This file previously rendered a single-article detail view that
 * expected a `:id` route param, but it's routed at `/articles` (no id) —
 * the destination of the Home page's "Start reading" button. That param
 * was always undefined, so the fetch always failed and nothing (including
 * no images) ever rendered here.
 *
 * This is now a proper full article feed page, consistent with the Home
 * page's article list — same ArticleCard, same tag filtering, same
 * "replace, don't append" behaviour.
 */
export default function Articles() {
  const [articles, setArticles] = useState([]);
  const [tags, setTags] = useState([]);
  const [activeTag, setActiveTag] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tagsLoading, setTagsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchArticles = async (tagSlug = null) => {
    setLoading(true);
    try {
      let url = endpoints.articles;
      if (tagSlug) {
        url += `?tags__slug=${encodeURIComponent(tagSlug)}`;
      }
      const res = await apiClient(url);
      if (!res.ok) throw new Error(`Articles API error: ${res.status}`);
      const data = await res.json();
      setArticles(data.results || data);
      setError(null);
    } catch (err) {
      console.error('[Articles] Error fetching articles:', err);
      setError(err.message || 'Failed to load articles.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const res = await apiClient(endpoints.tags);
        if (res.ok) {
          const data = await res.json();
          setTags(data.results || data);
        }
      } catch (err) {
        console.error('[Articles] Error fetching tags:', err);
      } finally {
        setTagsLoading(false);
      }
    };
    fetchTags();
  }, []);

  useEffect(() => {
    fetchArticles(activeTag);
  }, [activeTag]);

  const handleTagSelect = (tagSlug) => {
    setActiveTag(tagSlug);
  };

  if (error) return <div className="error container" style={{ padding: '48px 32px' }}>{error}</div>;

  return (
    <div className="container feed-layout">
      <main className="feed-main">
        <h2 className="feed-heading">{activeTag ? `#${activeTag}` : 'All stories'}</h2>
        <div className="feed-list">
          {loading ? (
            Array(5).fill().map((_, i) => <ArticleCard key={i} loading />)
          ) : articles.length === 0 ? (
            <p className="feed-empty">No articles found for this tag.</p>
          ) : (
            articles.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))
          )}
        </div>
      </main>
      <Sidebar
        activeTag={activeTag}
        onTagSelect={handleTagSelect}
        tags={tags}
        loading={tagsLoading}
      />
    </div>
  );
}