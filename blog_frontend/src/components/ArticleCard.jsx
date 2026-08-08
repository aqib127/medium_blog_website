import React from 'react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import SafeImage from './SafeImage';
import Avatar from './Avatar';
import SaveButton from './SaveButton';
import '../styles/article-card.css';

const ArticleCard = ({ article, loading, dense }) => {
  if (loading) {
    return (
      <div className="article-card--loading">
        <div className="article-card-skel-body">
          <div className="article-card-skel-line article-card-skel-line--author" />
          <div className="article-card-skel-line article-card-skel-line--title" />
          <div className="article-card-skel-line article-card-skel-line--text" />
          <div className="article-card-skel-line article-card-skel-line--text-short" />
        </div>
        <div className="article-card-skel-image" />
      </div>
    );
  }

  if (!article) return null;

  const author = article.author || {};
  const formattedDate = article.published_at || article.created_at
    ? formatDistanceToNow(new Date(article.published_at || article.created_at), { addSuffix: true })
    : '';
  const primaryTag = article.tags && article.tags.length > 0 ? article.tags[0].name : null;
  const excerpt = article.dek || (article.body ? article.body.replace(/<[^>]+>/g, '').slice(0, 160) + '…' : '');

  return (
    <div className={`article-card ${dense ? 'article-card--dense' : ''}`}>
      {/* Left: article info */}
      <div className="article-card-body">
        <Link to={`/@${author.handle}`} className="article-card-author">
          <Avatar name={author.name} avatar={author.avatar} color={author.avatar_color} size={20} />
          <span className="article-card-author-name">
            {author.name || 'Unknown author'}
          </span>
        </Link>

        <Link to={`/article/${article.id}`} className="article-card-link">
          <h2 className="article-card-title">{article.title}</h2>
          {excerpt && <p className="article-card-excerpt">{excerpt}</p>}
        </Link>

        <div className="article-card-meta">
          <div className="article-card-meta-left">
            {primaryTag && <span className="article-card-tag-pill">{primaryTag}</span>}
            {formattedDate && <span>{formattedDate}</span>}
            <span>·</span>
            <span>{article.read_mins || 1} min read</span>
          </div>

          <div className="article-card-stats">
            <span className="article-card-stat">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
              {article.claps_count || 0}
            </span>
            <span className="article-card-stat">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              {article.comments_count || 0}
            </span>
            <SaveButton articleId={article.id} />
          </div>
        </div>
      </div>

      {/* Right: fixed-size, consistent cover thumbnail */}
      <Link to={`/article/${article.id}`} className="article-card-image-link">
        <SafeImage
          src={article.image_url}
          alt={article.title}
          fallbackColor={article.cover_color || '#1F4E4A'}
        />
      </Link>
    </div>
  );
};

export default ArticleCard;