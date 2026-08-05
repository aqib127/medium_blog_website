import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import ArticleCard from '../components/ArticleCard';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import '../styles/search.css';

export default function Search() {
  const [params] = useSearchParams();
  const initialQuery = params.get('q') || '';
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState([]);
  const [tags, setTags] = useState([]);
  const [activeTag, setActiveTag] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const res = await apiClient(endpoints.tags);
        const data = await res.json();
        setTags(data);
      } catch (err) {
        console.error('Error fetching tags:', err);
      }
    };
    fetchTags();
  }, []);

  useEffect(() => {
    const search = async () => {
      if (!query.trim() && !activeTag) {
        setResults([]);
        return;
      }
      setLoading(true);
      try {
        let url = endpoints.articles + '?';
        if (query.trim()) url += `search=${encodeURIComponent(query.trim())}&`;
        if (activeTag) url += `tags=${activeTag}&`;
        const res = await apiClient(url);
        const data = await res.json();
        setResults(data.results || data);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setLoading(false);
      }
    };
    search();
  }, [query, activeTag]);

  const handleSubmit = (e) => { e.preventDefault(); };

  return (
    <div className="search-page container">
      <header className="search-header">
        <h1>Search Blog</h1>
        <form onSubmit={handleSubmit} className="search-bar">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by title, topic, or writer"
            autoFocus
          />
        </form>
        <div className="search-tags">
          <button className={!activeTag ? 'active' : ''} onClick={() => setActiveTag(null)}>All topics</button>
          {tags.map((t) => (
            <button
              key={t.id}
              className={activeTag === t.slug ? 'active' : ''}
              onClick={() => setActiveTag(t.slug)}
            >
              {t.name}
            </button>
          ))}
        </div>
      </header>
      <div className="search-results">
        <p className="search-count">{results.length} {results.length === 1 ? 'result' : 'results'}</p>
        {loading ? (
          Array(3).fill().map((_, i) => <ArticleCard key={i} loading dense />)
        ) : results.length ? (
          results.map((a) => <ArticleCard key={a.id} article={a} dense />)
        ) : (
          <p className="search-empty">Nothing matches yet. Try a different word or topic.</p>
        )}
      </div>
    </div>
  );
}