import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import ArticleCard from '../components/ArticleCard';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';

export default function Search() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSearchResults = async () => {
      if (!query) return setLoading(false);
      try {
        const res = await apiClient(`${endpoints.articles}?search=${query}`);
        if (res.ok) {
          const data = await res.json();
          setArticles(data.results || data);
        }
      } catch (err) {
        console.error("Search error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSearchResults();
  }, [query]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Search results for "{query}"</h1>
      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : articles.length === 0 ? (
        <p className="text-gray-500">No articles found.</p>
      ) : (
        articles.map(article => <ArticleCard key={article.id} article={article} />)
      )}
    </div>
  );
}