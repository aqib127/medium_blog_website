import { useEffect, useState } from "react";
import apiClient from "../utils/apiClient";
import { endpoints } from "../config/api";
import ArticleCard from "../components/ArticleCard";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";

export default function Articles() {
  const [loading, setLoading] = useState(true);
  const [articles, setArticles] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const articlesRes = await apiClient(endpoints.articles);
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

  if (loading) {
    return (
      <div style={{ padding: "50px", maxWidth: "780px", margin: "0 auto" }}>
        <Skeleton height={40} width={200} style={{ marginBottom: 24 }} />
        {[1, 2, 3].map((i) => (
          <ArticleCard key={i} loading />
        ))}
      </div>
    );
  }

  if (error) return <div className="error">{error}</div>;

  return (
    <div style={{ padding: "50px", maxWidth: "780px", margin: "0 auto" }}>
      <h1 style={{ fontFamily: "var(--font-display)", fontSize: "34px", marginBottom: "24px" }}>
        All Articles
      </h1>
      {articles.length === 0 ? (
        <p style={{ color: "var(--ink-soft)", padding: "40px 0", textAlign: "center" }}>
          No articles found.
        </p>
      ) : (
        articles.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))
      )}
    </div>
  );
}