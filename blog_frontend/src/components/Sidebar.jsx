import { Link } from "react-router-dom";
import { endpoints } from "../config/api";
import apiClient from "../utils/apiClient";
import { useEffect, useState } from "react";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import "../styles/sidebar.css";

export default function Sidebar({ activeTag, onTagSelect, tags, loading = false }) {
  const [trending, setTrending] = useState([]);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const res = await apiClient(endpoints.trending);
        const data = await res.json();
        setTrending(data);
      } catch (err) {
        console.error('Error fetching trending:', err);
      }
    };
    fetchTrending();
  }, []);

  if (loading) {
    return (
      <aside className="sidebar">
        <div className="sidebar-block">
          <h4 className="sidebar-heading"><Skeleton width={120} /></h4>
          <div className="tag-filters">
            <Skeleton width={60} height={30} />
            <Skeleton width={80} height={30} />
            <Skeleton width={70} height={30} />
          </div>
        </div>
        <div className="sidebar-block">
          <h4 className="sidebar-heading"><Skeleton width={100} /></h4>
          <ol className="trending-list">
            {[1,2,3].map(i => (
              <li key={i}><Skeleton count={2} /></li>
            ))}
          </ol>
        </div>
      </aside>
    );
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-block">
        <h4 className="sidebar-heading">Browse by topic</h4>
        <div className="tag-filters">
          <Link
            to="/"
            className={`tag-filter ${!activeTag ? "tag-filter--active" : ""}`}
            onClick={() => onTagSelect(null)}
          >
            All
          </Link>
          {tags.map((tag) => (
            <Link
              key={tag.id}
              to={`/tag/${tag.slug}`}
              className={`tag-filter ${activeTag === tag.slug ? "tag-filter--active" : ""}`}
              onClick={() => onTagSelect(tag.slug)}
            >
              {tag.name}
            </Link>
          ))}
        </div>
      </div>

      <div className="sidebar-block">
        <h4 className="sidebar-heading">Staff picks</h4>
        <ol className="trending-list">
          {trending.map((article, i) => {
            const author = article.author;
            if (!author) return null;
            return (
              <li key={article.id}>
                <span className="trending-index">{String(i + 1).padStart(2, "0")}</span>
                <div>
                  <Link to={`/@${author.handle}`} className="trending-byline">
                    {author.name}
                  </Link>
                  <Link to={`/article/${article.id}`} className="trending-title">
                    {article.title}
                  </Link>
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </aside>
  );
}