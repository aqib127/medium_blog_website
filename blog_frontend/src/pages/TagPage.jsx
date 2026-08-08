import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ArticleCard from '../components/ArticleCard';
import { getArticlesByTag } from '../utils/api';

export default function TagPage() {
  const { slug } = useParams();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTagArticles = async () => {
      try {
        const data = await getArticlesByTag(slug);
        setArticles(data);
      } catch (err) {
        console.error("Tag filter error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchTagArticles();
  }, [slug]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6 capitalize">Topic: {slug}</h1>
      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : articles.length === 0 ? (
        <p className="text-gray-500">No articles found for this tag.</p>
      ) : (
        <div className="flex flex-col">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}