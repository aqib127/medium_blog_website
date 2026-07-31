import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import ArticleCard from '../components/ArticleCard';
import '../styles/saved.css';

export default function SavedArticles() {
  const { user } = useAuth();
  const [savedArticles, setSavedArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    const fetchBookmarks = async () => {
      try {
        const res = await apiClient(endpoints.bookmarks);
        const data = await res.json();
        // Handle pagination
        const bookmarks = data.results || data;
        setSavedArticles(bookmarks.map((b) => b.article));
      } catch (err) {
        console.error('Error fetching bookmarks:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchBookmarks();
  }, [user]);

  if (!user) {
    return (
      <div className="saved-page container">
        <h1>Saved stories</h1>
        <p className="saved-empty">Please <a href="/signin">sign in</a> to view your saved stories.</p>
      </div>
    );
  }

  if (loading) return <div className="loading">Loading saved stories...</div>;

  return (
    <div className="saved-page container">
      <h1>Saved stories</h1>
      {savedArticles.length === 0 ? (
        <p className="saved-empty">You haven't saved any stories yet.</p>
      ) : (
        <div className="saved-list">
          {savedArticles.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      )}
    </div>
  );
}