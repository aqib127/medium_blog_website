import { useState, useEffect } from 'react';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import { useAuth } from '../context/AuthContext';
import '../styles/save-button.css';

export default function SaveButton({ articleId, initialSaved = null }) {
  const { user } = useAuth();
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // FIX: if the parent already knows the bookmarked state (e.g. the article
    // detail page passes article.is_bookmarked), use it directly and skip the
    // extra round-trip that used to fetch the ENTIRE bookmarks list on mount.
    if (initialSaved !== null) {
      setSaved(initialSaved);
      return;
    }
    if (!user) return;
    const checkSaved = async () => {
      try {
        const res = await apiClient(endpoints.bookmarks);
        const data = await res.json();
        // Handle pagination: if data has 'results', use that, else use data directly
        const bookmarks = data.results || data;
        const bookmarked = bookmarks.some((b) => b.article.id === articleId);
        setSaved(bookmarked);
      } catch (err) {
        console.error('Error checking bookmark:', err);
      }
    };
    checkSaved();
  }, [articleId, user, initialSaved]);

  const toggleSave = async () => {
    if (!user) {
      window.location.href = '/signin';
      return;
    }
    setLoading(true);
    try {
      if (saved) {
        const res = await apiClient(endpoints.bookmark(articleId), { method: 'DELETE' });
        if (res.ok || res.status === 404) {
          setSaved(false);
        }
      } else {
        const res = await apiClient(endpoints.bookmarks, {
          method: 'POST',
          body: JSON.stringify({ article_id: articleId }),
        });
        if (res.ok) {
          setSaved(true);
        } else if (res.status === 409) {
          // Already exists, sync state
          setSaved(true);
        }
      }
    } catch (err) {
      console.error('Bookmark error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className={`save-btn ${saved ? 'save-btn--saved' : ''}`}
      onClick={toggleSave}
      aria-label={saved ? 'Unsave this story' : 'Save this story'}
      disabled={loading}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {saved ? (
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" fill="currentColor" />
        ) : (
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" />
        )}
      </svg>
      <span>{saved ? 'Saved' : 'Save'}</span>
    </button>
  );
}