import React from 'react';
import { Link } from 'react-router-dom';
import SafeImage from './SafeImage';
import '../styles/drafts.css';

const DraftCard = ({ draft, onDelete }) => {
  if (!draft) return null;

  const excerpt =
    draft.dek ||
    (draft.body ? draft.body.replace(/<[^>]+>/g, '').slice(0, 140) + '…' : 'No subtitle');

  return (
    <li className="draft-card">
      {/* Left: draft info */}
      <div className="draft-card-body">
        <Link to={`/write?draft=${draft.id}`} className="draft-card-link">
          <h3 className="draft-card-title">{draft.title || 'Untitled draft'}</h3>
          <p className="draft-card-excerpt">{excerpt}</p>
        </Link>

        <div className="draft-card-footer">
          <span className="draft-card-date">
            Updated {new Date(draft.updated_at).toLocaleDateString()}
          </span>
          <button
            type="button"
            className="draft-card-delete"
            onClick={() => onDelete(draft.id)}
          >
            Delete
          </button>
        </div>
      </div>

      {/* Right: fixed-size, consistent thumbnail */}
      <Link to={`/write?draft=${draft.id}`} className="draft-card-image-link">
        <SafeImage
          src={draft.image_url}
          alt={draft.title || 'Untitled draft'}
          fallbackColor={draft.cover_color || '#1F4E4A'}
        />
      </Link>
    </li>
  );
};

export default DraftCard;