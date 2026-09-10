import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import Avatar from '../components/Avatar';
import ClapButton from '../components/ClapButton';
import SaveButton from '../components/SaveButton';
import FollowButton from '../components/FollowButton';
import CommentSection from '../components/CommentSection';
import RelatedArticleCard from '../components/RelatedArticleCard';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import '../styles/article.css';

export default function ArticleDetail() {
  const { id } = useParams();
  const [article, setArticle] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    const fetchArticle = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiClient(endpoints.article(id));
        if (!res.ok) {
          if (res.status === 404) throw new Error('Article not found');
          throw new Error(`Failed to load article: ${res.status}`);
        }
        const data = await res.json();
        if (!active) return;
        setArticle(data);

        try {
          const tagSlug = data.tags && data.tags[0] ? data.tags[0].slug : '';
          if (tagSlug) {
            const relatedRes = await apiClient(`${endpoints.articles}?tags__slug=${tagSlug}`);
            if (relatedRes.ok) {
              const relatedData = await relatedRes.json();
              const list = relatedData.results || relatedData;
              const filtered = list.filter((a) => a.id !== data.id);
              if (active) setRelated(filtered.slice(0, 3));
            }
          }
        } catch (err) {
          console.warn('Could not fetch related articles:', err);
        }
      } catch (err) {
        if (!active) return;
        setError(err.message || 'Failed to load article');
      } finally {
        if (active) setLoading(false);
      }
    };

    if (id) fetchArticle();
    return () => { active = false; };
  }, [id]);

  if (loading) {
    return (
      <div className="article-page container">
        <Skeleton height={40} width="70%" />
        <Skeleton height={20} width="40%" style={{ marginTop: 12 }} />
        <Skeleton height={300} style={{ marginTop: 24 }} />
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="article-page container" style={{ textAlign: 'center', padding: '80px 20px' }}>
        <h1>{error || 'Article not found'}</h1>
        <p>The article you are looking for does not exist or was removed.</p>
        <Link to="/" className="btn btn-primary" style={{ marginTop: 20 }}>Back to home</Link>
      </div>
    );
  }

  const author = article.author || {};

  return (
    <article className="article-page container">
      <header className="article-header">
        <h1 className="article-title">{article.title}</h1>
        {article.dek && <p className="article-dek">{article.dek}</p>}

        <div className="article-meta">
          <Link to={`/@${author.handle}`} className="article-author">
            <Avatar name={author.name} avatar={author.avatar} color={author.avatar_color} size={44} />
            <div>
              <strong>{author.name}</strong>
              <span>
                {article.published_at
                  ? new Date(article.published_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                  : ''}
                {article.reading_time ? ` · ${article.reading_time} min read` : ''}
              </span>
            </div>
          </Link>

          <div className="article-actions">
            <FollowButton handle={author.handle} />
            <SaveButton articleId={article.id} />
          </div>
        </div>
      </header>

      <div className="article-body" dangerouslySetInnerHTML={{ __html: article.body || '' }} />

      <footer className="article-footer">
        <ClapButton articleId={article.id} initialClaps={article.claps_count || 0} />
        {article.tags && article.tags.length > 0 && (
          <div className="article-tags">
            {article.tags.map((tag) => (
              <Link key={tag.id} to={`/tag/${tag.slug}`} className="article-tag">#{tag.name}</Link>
            ))}
          </div>
        )}
      </footer>

      <CommentSection articleId={article.id} />

      {related.length > 0 && (
        <section className="article-related">
          <h2>More from {author.name}</h2>
          <div className="related-grid">
            {related.map((a) => (
              <RelatedArticleCard key={a.id} article={a} />
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
