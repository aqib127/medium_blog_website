import { Link, useNavigate } from "react-router-dom";
import Avatar from "./Avatar";
import "../styles/article-card.css";

export default function ArticleCard({ article, dense = false }) {
  const navigate = useNavigate();

  if (!article || !article.author) return null;

  const { author } = article;

  const handleTagClick = (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (article.tags?.[0]?.slug) {
      navigate(`/tag/${article.tags[0].slug}`);
    }
  };

  return (
    <article className={`a-card ${dense ? "a-card--dense" : ""}`}>
      <Link
        to={`/@${author.handle}`}
        className="a-card-author"
      >
        <Avatar
          name={author.name}
          avatar={author.avatar}
          color={author.avatar_color}
          size={26}
        />

        <span>{author.name}</span>
      </Link>

      <Link
        to={`/article/${article.id}`}
        className="a-card-content"
      >
        <div className="a-card-left">

          <h2 className="a-card-title">
            {article.title}
          </h2>

          {!dense && article.dek && (
            <p className="a-card-description">
              {article.dek}
            </p>
          )}

          <div className="a-card-footer">

            {article.tags?.length > 0 && (
              <span
                className="tag-pill"
                onClick={handleTagClick}
              >
                {article.tags[0].name}
              </span>
            )}

            <span>{article.read_mins} min read</span>

          </div>

        </div>

        <div
          className="a-card-image"
          style={{
            background: article.cover_color || "#f2f2f2",
          }}
        >
          <span>{article.folio}</span>
        </div>
      </Link>
    </article>
  );
}