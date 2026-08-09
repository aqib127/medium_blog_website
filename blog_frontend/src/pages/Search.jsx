import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ArticleCard from '../components/ArticleCard';
import Sidebar from '../components/Sidebar';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import '../styles/search.css';

export default function Search() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q') || '';
  const [articles, setArticles] = useState([]);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tagsLoading, setTagsLoading] = useState(true);
  const [activeTag, setActiveTag] = useState(null);
  const [draft, setDraft] = useState(query);

  useEffect(() => {
    const fetchSearchResults = async () => {
      if (!query) return setLoading(false);
      setLoading(true);
      try {
        const res = await apiClient(`${endpoints.articles}?search=${encodeURIComponent(query)}`);
        if (res.ok) {
          const data = await res.json();
          setArticles(data.results || data);
        }
      } catch (err) {
        console.error("Search error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSearchResults();
  }, [query]);

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

  const submitSearch = (e) => {
    e.preventDefault();
    if (draft.trim()) navigate(`/search?q=${encodeURIComponent(draft.trim())}`);
  };

  const handleTagSelect = (tagSlug) => {
    setActiveTag(tagSlug);
    if (tagSlug) navigate(`/tag/${tagSlug}`);
  };

  return (
    <div className="container feed-layout">
      <main className="feed-main">
        <div className="search-page">
          <header className="search-header">
            <h1>{query ? `Results for "${query}"` : 'Search'}</h1>
            <form className="search-bar" onSubmit={submitSearch}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              <input
                type="text"
                placeholder="Search essays, ideas, writers"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                aria-label="Search"
              />
            </form>
          </header>

          {loading ? (
            Array(4).fill().map((_, i) => <ArticleCard key={i} loading />)
          ) : articles.length === 0 ? (
            <p className="search-empty">No articles found{query ? ` for "${query}"` : ''}.</p>
          ) : (
            <>
              <p className="search-count">{articles.length} result{articles.length === 1 ? '' : 's'}</p>
              {articles.map((article) => (
                <ArticleCard key={article.id} article={article} activeTag={activeTag} />
              ))}
            </>
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
