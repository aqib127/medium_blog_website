import { useEffect, useRef, useState } from 'react';
import { useParams, Link, Navigate } from 'react-router-dom';
import DOMPurify from 'dompurify';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import { useAuth } from '../context/AuthContext';
import ClapButton from '../components/ClapButton';
import FollowButton from '../components/FollowButton';
import CommentSection from '../components/CommentSection';
import SaveButton from '../components/SaveButton';
import Avatar from '../components/Avatar';
import SafeImage from '../components/SafeImage';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import '../styles/article.css';

export default function Article() {
  const { id } = useParams();
  const { user } = useAuth();
  const [article, setArticle] = useState(null);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showComments, setShowComments] = useState(false);
  const bodyRef = useRef(null);
  const commentsRef = useRef(null);

  const fetchArticle = async () => {
    try {
      const articleRes = await apiClient(endpoints.article(id));
      if (!articleRes.ok) throw new Error('Article not found');
      const articleData = await articleRes.json();
      setArticle(articleData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticle();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    const onScroll = () => {
      if (!bodyRef.current) return;
      const rect = bodyRef.current.getBoundingClientRect();
      const total = rect.height - window.innerHeight * 0.5;
      const scrolled = -rect.top;
      const pct = Math.min(100, Math.max(0, (scrolled / total) * 100));
      setProgress(pct || 0);
    };
    window.addEventListener('scroll', onScroll);
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, [id]);

  const handleCommentAdded = (newCount) => {
    setArticle((prev) => (prev ? { ...prev, comments_count: newCount } : prev));
  };

  const toggleComments = () => {
    setShowComments(!showComments);
    if (!showComments) {
      setTimeout(() => {
        commentsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  };

  if (loading) {
    return (
      <article className="reader">
        <div className="reader-content container">
          <Skeleton height={320} borderRadius={12} style={{ marginBottom: 32 }} />
          <header className="reader-header">
            <Skeleton width={100} />
            <Skeleton height={60} count={2} />
            <Skeleton height={30} count={3} />
            <div className="reader-byline">
              <Skeleton circle width={46} height={46} />
              <div>
                <Skeleton width={150} />
                <Skeleton width={100} />
              </div>
            </div>
            <div className="reader-actions">
              <Skeleton width={80} height={36} />
              <Skeleton width={80} height={36} />
            </div>
          </header>
          <div className="reader-body">
            <Skeleton count={8} />
          </div>
        </div>
      </article>
    );
  }

  if (!article) return <Navigate to="/" replace />;

  const author = article.author;
  const statusLabel = article.status
    ? article.status.charAt(0).toUpperCase() + article.status.slice(1)
    : '';

  return (
    <article className="reader">
      <div className="reader-margin" aria-hidden="true">
        <div className="folio-rail">
          <span className="folio-number">No. {article.folio || '---'}</span>
          <div className="folio-meta">
            <span className="folio-meta-row">ID · {article.id}</span>
            <span className="folio-meta-row">Type · {statusLabel}</span>
          </div>
          <div className="folio-track">
            <div className="folio-fill" style={{ height: `${progress}%` }} />
          </div>
          <span className="folio-tag">{article.tags?.[0]?.name || ''}</span>
        </div>
      </div>

      <div className="reader-content container">
        {/* Larger featured cover image — as required across the app's image spec */}
        <div className="w-full h-64 sm:h-96 rounded-xl overflow-hidden mb-8 shadow-sm">
          <SafeImage
            src={article.image_url}
            alt={article.title}
            fallbackColor={article.cover_color || '#1F4E4A'}
          />
        </div>

        <header className="reader-header">
          <span className="eyebrow">{article.tags?.[0]?.name || ''}</span>
          <h1>{article.title}</h1>
          <p className="reader-dek">{article.dek}</p>

          <div className="reader-byline">
            <Link to={`/@${author.handle}`}>
              <Avatar
                name={author.name}
                avatar={author.avatar}
                color={author.avatar_color}
                size={46}
              />
            </Link>
            <div className="reader-byline-text">
              <Link to={`/@${author.handle}`} className="reader-author-name">{author.name}</Link>
              <span className="reader-byline-meta">
                {article.read_mins} min read · {new Date(article.published_at || article.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
              </span>
            </div>
            {/* FIX: Medium shows a follow control next to the byline, but you
                can't follow yourself — the backend returns 400 ("You cannot
                follow yourself."). Only show it when the author isn't you. */}
            {user && author.handle !== user.handle && (
              <FollowButton handle={author.handle} className="reader-follow-btn" />
            )}
          </div>
        </header>

        <div className="reader-body" ref={bodyRef}>
          {/* FIX: sanitize before injecting — author content can contain
              arbitrary HTML that would otherwise allow stored XSS. */}
          <div
            className="reader-body-html"
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(article.body) }}
          />
        </div>

        <div className="reader-actions reader-actions--footer">
          {/* FIX: key the interactive buttons by article id so their local
              state (clap count, saved state) resets when navigating from
              one story to the next — React Router reuses the same component
              instance across /article/:id transitions, so useState() alone
              would otherwise carry stale clap/save state between articles. */}
          <ClapButton key={article.id} articleId={article.id} initialClaps={article.claps_count} initialClapped={article.is_clapped} />
          <SaveButton key={article.id} articleId={article.id} initialSaved={article.is_bookmarked} />
          <button
            className="reader-comment-toggle"
            onClick={toggleComments}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              background: 'none',
              border: 'none',
              color: 'var(--ink-soft)',
              cursor: 'pointer',
              font: 'inherit',
              padding: 0,
            }}
            aria-expanded={showComments}
          >
            💬 {article.comments_count} responses {showComments ? '▲' : '▼'}
          </button>
        </div>

        <div
          ref={commentsRef}
          id="comments"
          style={{
            scrollMarginTop: '80px',
            display: showComments ? 'block' : 'none',
          }}
        >
          <CommentSection
            articleId={article.id}
            initialCount={article.comments_count}
            onCommentAdded={handleCommentAdded}
          />
        </div>
      </div>
    </article>
  );
}