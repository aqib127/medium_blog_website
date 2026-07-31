import { Link } from "react-router-dom";
import Avatar from "./Avatar";
import "../styles/article-card.css";

export default function ArticleCard({ article, dense }) {
  // article.author is the nested user object from API
  const author = article.author;

  if (!author) {
    return null; // fallback if no author
  }

  return (
    <article className={`a-card ${dense ? "a-card--dense" : ""}`}>
      <Link to={`/@${author.handle}`} className="a-card-byline">
        <Avatar
          name={author.name}
          avatar={author.avatar}
          color={author.avatar_color}
          size={22}
        />
        {author.name}
      </Link>

      <Link to={`/article/${article.id}`} className="a-card-body">
        <div className="a-card-text">
          <h3>{article.title}</h3>
          {!dense && <p className="a-card-dek">{article.dek}</p>}
          <div className="a-card-meta">
            <Link to={`/tag/${article.tags?.[0]?.slug || ''}`} className="tag-pill">
              {article.tags?.[0]?.name || ''}
            </Link>
            <span className="dot">·</span>
            <span>{article.read_mins} min read</span>
          </div>
        </div>
        <span className="a-card-cover" style={{ background: article.cover_color }} aria-hidden="true">
          <span className="a-card-folio">{article.folio}</span>
        </span>
      </Link>
    </article>
  );
}