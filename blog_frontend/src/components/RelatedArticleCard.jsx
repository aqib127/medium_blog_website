import React from 'react';
import { Link } from 'react-router-dom';
import SafeImage from './SafeImage';
import '../styles/related-article-card.css';

const RelatedArticleCard = ({ article }) => {
  if (!article) return null;

  const authorInitials = article.author?.username?.substring(0, 2).toUpperCase() || '?';
  const primaryTag = article.tags && article.tags.length > 0 ? article.tags[0].name : 'General';

  return (
    <div className="related-article-card">
      {/* Left: article info */}
      <div className="related-article-body">
        <div className="related-article-author">
          <span className="related-article-author-initials">{authorInitials}</span>
          <span>{article.author?.username}</span>
        </div>
        <Link to={`/article/${article.id}`}>
          <h4 className="related-article-title">{article.title}</h4>
        </Link>
        <span className="related-article-footer">
          {article.read_mins || 1} min read · {primaryTag}
        </span>
      </div>

      {/* Right: fixed-size, consistent thumbnail */}
      <Link to={`/article/${article.id}`} className="related-article-image-link">
        <SafeImage
          src={article.image_url}
          alt={article.title}
          fallbackColor={article.cover_color || '#1F4E4A'}
        />
      </Link>
    </div>
  );
};

export default RelatedArticleCard;