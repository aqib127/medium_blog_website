import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import ArticleCard from '../components/ArticleCard';
import Sidebar from '../components/Sidebar';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import '../styles/home.css';

const FEEDS = [
  { key: 'for-you', label: 'For you' },
  { key: 'following', label: 'Following' },
];

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [featured, setFeatured] = useState(null);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTag, setActiveTag] = useState(null);
  const [feed, setFeed] = useState('for-you');

  const buildUrl = (tagSlug, activeFeed) => {
    const params = new URLSearchParams();
    if (tagSlug) {
      // Correct Django filter param: tags__slug
      params.set('tags__slug', tagSlug);
    }
    if (activeFeed === 'following') {
      params.set('feed', 'following');
    }
    const qs = params.toString();
    return qs ? `${endpoints.articles}?${qs}` : endpoints.articles;
  };

  const fetchArticles = async (tagSlug = null, activeFeed = feed) => {
    setLoading(true);
    try {
      const res = await apiClient(buildUrl(tagSlug, activeFeed));
      if (!res.ok) throw new Error(`Articles API error: ${res.status}`);
      const data = await res.json();
      // Always replace results — never append — so switching never mixes lists.
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

  // Re-fetch whenever the active tag or feed changes — replaces previous results.
  useEffect(() => {
    fetchArticles(activeTag, feed);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTag, feed]);

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

          {/* Medium-style feed tabs: "For you" and (when signed in) "Following". */}
          <div className="feed-tabs" role="tablist" aria-label="Feed">
            {FEEDS.map(({ key, label }) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={feed === key}
                className={`feed-tab ${feed === key ? 'feed-tab--active' : ''}`}
                onClick={() => setFeed(key)}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="feed-list">
            {loading ? (
              Array(3).fill().map((_, i) => <ArticleCard key={i} loading dense />)
            ) : articles.length === 0 ? (
              <p style={{ padding: '40px 0', color: 'var(--ink-soft)', textAlign: 'center' }}>
                {feed === 'following'
                  ? 'Stories from writers you follow will appear here. Follow some authors to build your feed.'
                  : activeTag
                    ? 'No articles found for this tag.'
                    : 'No stories yet.'}
              </p>
            ) : (
              articles.map((article) => (
                <ArticleCard key={article.id} article={article} activeTag={activeTag} />
              ))
            )}
          </div>
        </main>
        <Sidebar activeTag={activeTag} onTagSelect={handleTagSelect} tags={tags} loading={loading && tags.length === 0} />
      </div>
    </>
  );
}