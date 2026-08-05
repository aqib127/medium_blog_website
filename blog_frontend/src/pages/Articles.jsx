import { useEffect, useState } from "react";
import apiClient from "../utils/apiClient";
import { endpoints } from "../config/api";
import ArticleCard from "../components/ArticleCard";

export default function Articles() {
  const [loading, setLoading] = useState(true);
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const articlesRes = await apiClient(endpoints.articles);

        // Check each response
        if (!articlesRes.ok)
          throw new Error(`Articles API error: ${articlesRes.status}`);

        const articlesData = await articlesRes.json();

        setArticles(articlesData.results || articlesData);
      } catch (err) {
        console.error("Error loading articles:", err);
        setError(err.message || "Failed to load content. Please refresh.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div style={{ padding: "50px" }}>
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}
