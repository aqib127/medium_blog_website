import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import ArticleCard from '../components/ArticleCard';
import '../styles/tag.css';

export default function TagPage() {
  const { tagName } = useParams();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTagArticles = async () => {
      try {
        const res = await apiClient(`${endpoints.articles}?tags=${tagName}`);
        const data = await res.json();
        setArticles(data.results || data);
      } catch (err) {
        console.error('Error fetching tag articles:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTagArticles();
  }, [tagName]);

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="tag-page container">
      <header className="tag-header">
        <h1>#{tagName}</h1>
        <p>{articles.length} stories</p>
      </header>
      {articles.length === 0 ? (
        <p className="tag-empty">No stories found with this tag.</p>
      ) : (
        <div className="tag-stories">
          {articles.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      )}
    </div>
  );
}