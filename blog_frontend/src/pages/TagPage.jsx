import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ArticleCard from '../components/ArticleCard';
import Sidebar from '../components/Sidebar';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import '../styles/tag.css';

export default function TagPage() {
  const { slug } = useParams();
  const [articles, setArticles] = useState([]);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tagsLoading, setTagsLoading] = useState(true);
  const [activeTag, setActiveTag] = useState(null);

  useEffect(() => {
    const fetchTagArticles = async () => {
      setLoading(true);
      try {
        // FIX: use the same apiClient + endpoints pattern as the rest of the
        // app (this page used the deleted utils/api.js wrapper).
        const res = await apiClient(`${endpoints.articles}?tags__slug=${encodeURIComponent(slug)}`);
        if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
        const data = await res.json();
        setArticles(data.results || data);
      } catch (err) {
        console.error('Tag filter error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTagArticles();
  }, [slug]);

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const res = await apiClient(endpoints.tags);
        if (res.ok) {
          const data = await res.json();
          setTags(data.results || data);
        }
      } catch (err) {
        console.error('Failed to fetch tags', err);
      } finally {
        setTagsLoading(false);
      }
    };
    fetchTags();
  }, []);

  const handleTagSelect = (tagSlug) => {
    setActiveTag(tagSlug);
    // Navigate to the chosen topic route for a proper tagged feed.
    if (tagSlug) window.location.href = `/tag/${tagSlug}`;
  };

  return (
    <div className="container feed-layout">
      <main className="feed-main">
        <div className="tag-page">
          <header className="tag-header">
            <h1 className="capitalize">{slug}</h1>
            <p>Stories written about this topic.</p>
          </header>
          {loading ? (
            Array(4).fill().map((_, i) => <ArticleCard key={i} loading />)
          ) : articles.length === 0 ? (
            <p className="tag-empty">No articles found for this tag.</p>
          ) : (
            articles.map((article) => (
              <ArticleCard key={article.id} article={article} activeTag={slug} />
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
