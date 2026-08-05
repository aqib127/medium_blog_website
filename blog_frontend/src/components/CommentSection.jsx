import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { endpoints } from "../config/api";
import apiClient from "../utils/apiClient";
import Avatar from "./Avatar";
import "../styles/comments.css";

export default function CommentSection({ articleId, initialCount = 0 }) {
  const { user } = useAuth();
  const [comments, setComments] = useState([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetchComments = async () => {
      if (!articleId) return;
      try {
        const res = await apiClient(endpoints.commentList(articleId));
        const data = await res.json();
        setComments(data.results || data);
      } catch (err) {
        console.error('Error fetching comments:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchComments();
  }, [articleId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!draft.trim() || submitting) return;
    setSubmitting(true);
    try {
      const res = await apiClient(endpoints.comments, {
        method: 'POST',
        body: JSON.stringify({
          article: articleId,
          text: draft.trim(),
        }),
      });
      if (res.ok) {
        const newComment = await res.json();
        setComments(prev => [newComment, ...prev]);
        setDraft("");
      }
    } catch (err) {
      console.error('Error posting comment:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="comments-loading">Loading comments...</div>;

  return (
    <section className="comments">
      <h3 className="comments-heading">Responses ({comments.length + initialCount})</h3>

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
              disabled={submitting}
            />
            <button className="btn btn-primary" type="submit" disabled={!draft.trim() || submitting}>
              {submitting ? 'Posting...' : 'Respond'}
            </button>
          </div>
        </form>
      ) : (
        <p className="comments-signin-hint">
          <a href="/signin">Sign in</a> to leave a response.
        </p>
      )}

      <ul className="comment-list">
        {comments.length === 0 ? (
          <li className="no-comments">No comments yet. Be the first to respond!</li>
        ) : (
          comments.map((c) => (
            <li key={c.id} className="comment-item">
              <Avatar
                name={c.author.name}
                avatar={c.author.avatar}
                color={c.author.avatar_color}
                size={34}
              />
              <div>
                <div className="comment-meta">
                  <strong>{c.author.name}</strong>
                  <span>{new Date(c.created_at).toLocaleDateString()}</span>
                </div>
                <p>{c.text}</p>
              </div>
            </li>
          ))
        )}
      </ul>
    </section>
  );
}