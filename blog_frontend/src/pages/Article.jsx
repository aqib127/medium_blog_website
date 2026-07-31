import { useEffect, useRef, useState } from 'react';
import { useParams, Link, Navigate } from 'react-router-dom';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import { useAuth } from '../context/AuthContext';
import ClapButton from '../components/ClapButton';
import CommentSection from '../components/CommentSection';
import SaveButton from '../components/SaveButton';
import Avatar from '../components/Avatar';
import '../styles/article.css';

export default function Article() {
  const { id } = useParams();
  const [article, setArticle] = useState(null);
  const [comments, setComments] = useState([]);
  const [progress, setProgress] = useState(0);
  const [following, setFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const bodyRef = useRef(null);

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        const [articleRes, commentsRes] = await Promise.all([
          apiClient(endpoints.article(id)),
          apiClient(endpoints.commentList(id)),
        ]);
        if (!articleRes.ok) throw new Error('Article not found');
        const articleData = await articleRes.json();
        const commentsData = commentsRes.ok ? await commentsRes.json() : [];
        setArticle(articleData);
        setComments(commentsData.results || commentsData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchArticle();
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

  if (loading) return <div className="loading">Loading article...</div>;
  if (!article) return <Navigate to="/" replace />;

  const author = article.author;

  return (
    <article className="reader">
      <div className="reader-margin" aria-hidden="true">
        <div className="folio-rail">
          <span className="folio-number">No. {article.folio || '---'}</span>
          <div className="folio-track">
            <div className="folio-fill" style={{ height: `${progress}%` }} />
          </div>
          <span className="folio-tag">{article.tags?.[0]?.name || ''}</span>
        </div>
      </div>

      <div className="reader-content container">
        <header className="reader-header">
          <span className="eyebrow">{article.tags?.[0]?.name || ''}</span>
          <h1>{article.title}</h1>
          <p className="reader-dek">{article.dek}</p>

          <div className="reader-byline">
            <Link to={`/@${author.handle}`}>
              <Avatar name={author.name} avatar={author.avatar} color={author.avatar_color} size={46} />
            </Link>
            <div className="reader-byline-text">
              <Link to={`/@${author.handle}`} className="reader-author-name">{author.name}</Link>
              <span className="reader-byline-meta">
                {article.read_mins} min read · {new Date(article.published_at || article.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
              </span>
            </div>
            <button
              className={`btn ${following ? 'btn-ghost' : 'btn-primary'} reader-follow`}
              onClick={() => setFollowing((f) => !f)}
            >
              {following ? 'Following' : 'Follow'}
            </button>
          </div>

          <div className="reader-actions">
            <ClapButton articleId={article.id} initialClaps={article.claps_count} />
            <SaveButton articleId={article.id} />
            <span className="reader-comment-count">💬 {article.comments_count} responses</span>
          </div>
        </header>

        <div className="reader-body" ref={bodyRef}>
          {article.body.split('\n').map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>

        <div className="reader-actions reader-actions--footer">
          <ClapButton articleId={article.id} initialClaps={article.claps_count} />
          <SaveButton articleId={article.id} />
        </div>

        <CommentSection articleId={article.id} initialCount={article.comments_count} />
      </div>
    </article>
  );
}