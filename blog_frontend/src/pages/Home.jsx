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

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [articlesRes, featuredRes, tagsRes] = await Promise.all([
          apiClient(endpoints.articles),
          apiClient(endpoints.featured),
          apiClient(endpoints.tags),
        ]);

        if (!articlesRes.ok) throw new Error(`Articles API error: ${articlesRes.status}`);
        if (!tagsRes.ok) throw new Error(`Tags API error: ${tagsRes.status}`);

        const articlesData = await articlesRes.json();
        const featuredData = featuredRes.ok ? await featuredRes.json() : null;
        const tagsData = await tagsRes.json();

        setArticles(articlesData.results || articlesData);
        setFeatured(featuredData);
        setTags(tagsData);
      } catch (err) {
        console.error('Error loading home:', err);
        setError(err.message || 'Failed to load content. Please refresh.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredArticles = activeTag
    ? articles.filter((a) => a.tags?.some((t) => t.slug === activeTag))
    : articles;

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
              <Link to="/signup" className="btn btn-primary">Start reading</Link>
              <Link to="/write" className="btn btn-ghost">Start writing</Link>
            </div>
          </div>
          {loading ? (
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

      <div className="container feed-layout">
        <main className="feed-main">
          <h2 className="feed-heading">{activeTag ? `#${activeTag}` : 'Latest'}</h2>
          <div className="feed-list">
            {loading ? (
              Array(3).fill().map((_, i) => <ArticleCard key={i} loading dense />)
            ) : (
              filteredArticles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))
            )}
          </div>
        </main>
        <Sidebar activeTag={activeTag} onTagSelect={setActiveTag} tags={tags} loading={loading} />
      </div>
    </>
  );
}