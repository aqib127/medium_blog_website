import { Link } from "react-router-dom";
import { endpoints } from "../config/api";
import apiClient from "../utils/apiClient";
import { useEffect, useState } from "react";
import Avatar from "./Avatar";
import "../styles/sidebar.css";

export default function Sidebar({ activeTag, onTagSelect, tags }) {
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

      <div className="sidebar-block">
        <h4 className="sidebar-heading">Writers to follow</h4>
        <ul className="writer-list">
          {/* For now, we can still use mock users, or we could fetch from API */}
          {/* We'll keep mock users for simplicity, but better to fetch from API later */}
          {/* Temporarily keep existing mock users until we have an endpoint */}
        </ul>
      </div>
    </aside>
  );
}