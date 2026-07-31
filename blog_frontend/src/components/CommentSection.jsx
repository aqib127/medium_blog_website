import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import Avatar from "./Avatar";
import "../styles/comments.css";

const seedComments = [
  {
    id: "c1",
    name: "Rosa Bianchi",
    color: "#1F4E4A",
    time: "2 days ago",
    text: "This reframed something I've felt for years but never had words for. Saving this one.",
  },
  {
    id: "c2",
    name: "Devon Achebe",
    color: "#B8862E",
    time: "1 day ago",
    text: "Disagree with the framing in the third section, but the rest holds up. Well argued throughout.",
  },
];

export default function CommentSection({ count }) {
  const { user } = useAuth();
  const [comments, setComments] = useState(seedComments);
  const [draft, setDraft] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!draft.trim()) return;
    setComments((c) => [
      {
        id: `c${Date.now()}`,
        name: user?.name || "You",
        color: user?.avatarColor || "#1F4E4A",
        avatar: user?.avatar || null,
        time: "just now",
        text: draft.trim(),
      },
      ...c,
    ]);
    setDraft("");
  };

  return (
    <section className="comments">
      <h3 className="comments-heading">Responses ({count + comments.length - seedComments.length})</h3>

      {user ? (
        <form className="comment-form" onSubmit={handleSubmit}>
          <Avatar
            name={user.name}
            avatar={user.avatar}
            color={user.avatarColor}
            size={34}
          />
          <div className="comment-form-field">
            <textarea
              placeholder="What are your thoughts?"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={2}
            />
            <button className="btn btn-primary" type="submit" disabled={!draft.trim()}>
              Respond
            </button>
          </div>
        </form>
      ) : (
        <p className="comments-signin-hint">
          <a href="/signin">Sign in</a> to leave a response.
        </p>
      )}

      <ul className="comment-list">
        {comments.map((c) => (
          <li key={c.id} className="comment-item">
            <Avatar
              name={c.name}
              avatar={c.avatar}
              color={c.color}
              size={34}
            />
            <div>
              <div className="comment-meta">
                <strong>{c.name}</strong>
                <span>{c.time}</span>
              </div>
              <p>{c.text}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}