import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import ArticleCard from '../components/ArticleCard';
import Sidebar from '../components/Sidebar';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import '../styles/home.css';

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [featured, setFeatured] = useState(null);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTag, setActiveTag] = useState(null);

  const fetchArticles = async (tagSlug = null) => {
    setLoading(true);
    try {
      let url = endpoints.articles;
      if (tagSlug) {
        // Correct Django filter param: tags__slug
        url += `?tags__slug=${encodeURIComponent(tagSlug)}`;
      }
      const res = await apiClient(url);
      if (!res.ok) throw new Error(`Articles API error: ${res.status}`);
      const data = await res.json();
      // Always replace results — never append — so switching tags never mixes lists.
      setArticles(data.results || data);
      setError(null);
    } catch (err) {
      console.error('[Home] Error fetching articles:', err);
      setError(err.message || 'Failed to load articles.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchMeta = async () => {
      try {
        const [featuredRes, tagsRes] = await Promise.all([
          apiClient(endpoints.featured),
          apiClient(endpoints.tags),
        ]);
        const featuredData = featuredRes.ok ? await featuredRes.json() : null;
        const tagsData = tagsRes.ok ? await tagsRes.json() : [];
        setFeatured(featuredData);
        setTags(tagsData.results || tagsData);
      } catch (err) {
        console.error('[Home] Error fetching meta data:', err);
      }
    };
    fetchMeta();
  }, []);

  // Re-fetch whenever the active tag changes — completely replaces previous results.
  useEffect(() => {
    fetchArticles(activeTag);
  }, [activeTag]);

  const handleTagSelect = (tagSlug) => {
    setActiveTag(tagSlug);
  };

  if (error) return <div className="error">{error}</div>;

  const featuredAuthor = featured?.author;

  return (
    <>
      <section className="hero">
        <div className="container hero-inner">
          <div className="hero-copy">
            <span className="eyebrow">The second reading</span>
            <h1>Essays and ideas <em>worth</em> turning the page for.</h1>
            <p>Blog is a place for writing that rewards a second look — long-form journalism, craft essays, and arguments that hold up on the reread.</p>
            <div className="hero-actions">
              <Link to="/articles" className="btn btn-primary">Start reading</Link>
              <Link to="/write" className="btn btn-ghost">Start writing</Link>
            </div>
          </div>
          {loading && !featured ? (
            <div className="hero-cover" style={{ aspectRatio: '4/5' }}>
              <Skeleton height="100%" />
            </div>
          ) : featured && featuredAuthor ? (
            <Link to={`/article/${featured.id}`} className="hero-cover" style={{ background: featured.cover_color }}>
              <span className="hero-folio">No. {featured.folio || '---'}</span>
              <div className="hero-cover-text">
                <span className="hero-cover-tag">{featured.tags?.[0]?.name || ''}</span>
                <h2>{featured.title}</h2>
                <span className="hero-cover-byline">{featuredAuthor.name}</span>
              </div>
            </Link>
          ) : null}
        </div>
      </section>

      <div className="feed-layout">
        <main className="feed-main">
          <h2 className="feed-heading">{activeTag ? `#${activeTag}` : 'Latest'}</h2>
          <div className="feed-list">
            {loading ? (
              Array(3).fill().map((_, i) => <ArticleCard key={i} loading dense />)
            ) : articles.length === 0 ? (
              <p style={{ padding: '40px 0', color: 'var(--ink-soft)', textAlign: 'center' }}>
                No articles found for this tag.
              </p>
            ) : (
              articles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))
            )}
          </div>
        </main>
        <Sidebar activeTag={activeTag} onTagSelect={handleTagSelect} tags={tags} loading={loading && tags.length === 0} />
      </div>
    </>
  );
}