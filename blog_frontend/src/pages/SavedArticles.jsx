import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import ArticleCard from '../components/ArticleCard';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';

export default function SavedArticles() {
  const { user } = useAuth();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSaved = async () => {
      if (!user) return setLoading(false);
      try {
        const res = await apiClient(endpoints.bookmarks);
        if (res.ok) {
          const data = await res.json();
          // Bookmarks return objects, parse them into articles.
          setArticles(data.results ? data.results.map(b => b.article) : data.map(b => b.article));
        }
      } catch (err) {
        console.error("Failed to fetch saved articles", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSaved();
  }, [user]);

  if (!user) return <div className="text-center py-10">Please sign in to view your saved articles.</div>;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Your Reading List</h1>
      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : articles.length === 0 ? (
        <p className="text-gray-500">You haven't saved any articles yet.</p>
      ) : (
        articles.map(article => <ArticleCard key={article.id} article={article} />)
      )}
    </div>
  );
}