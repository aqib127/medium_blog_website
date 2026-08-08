import React from 'react';
import { Link } from 'react-router-dom';
import SafeImage from './SafeImage';

const DraftCard = ({ draft, onDelete }) => {
  return (
    <div className="flex items-center gap-4 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors px-2 rounded-lg">
      <Link to={`/write?draft=${draft.id}`} className="flex-shrink-0 w-14 h-10 rounded overflow-hidden bg-gray-100 relative shadow-sm">
        <SafeImage 
          src={draft.image_url} 
          alt={draft.title} 
          fallbackColor={draft.cover_color || '#1F4E4A'}
        />
      </Link>
      <Link to={`/write?draft=${draft.id}`} className="flex-1 profile-draft-link">
        <h3 className="text-base font-semibold text-gray-800 hover:text-blue-600 transition-colors">
          {draft.title || 'Untitled draft'}
        </h3>
        <p className="text-sm text-gray-500">{draft.dek || 'No subtitle'}</p>
        <span className="text-xs text-gray-400 mt-1 block">
          Updated {new Date(draft.updated_at).toLocaleDateString()}￼
        </span>
      </Link>
      <button 
        className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors ml-auto flex-shrink-0"
        onClick={() => onDelete(draft.id)}
      >
        Delete
      </button>
    </div>
  );
};

export default DraftCard;