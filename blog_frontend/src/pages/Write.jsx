import { useState, useEffect } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import '../styles/write.css';

export default function Write() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const draftId = searchParams.get('draft');

  const [title, setTitle] = useState('');
  const [dek, setDek] = useState('');
  const [tag, setTag] = useState('');
  const [body, setBody] = useState('');
  const [tags, setTags] = useState([]);
  const [published, setPublished] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const res = await apiClient(endpoints.tags);
        const data = await res.json();
        setTags(data);
        if (data.length) setTag(data[0].slug);
      } catch (err) {
        console.error('Error fetching tags:', err);
      }
    };
    fetchTags();
  }, []);

  useEffect(() => {
    if (draftId) {
      const fetchDraft = async () => {
        try {
          const res = await apiClient(endpoints.article(draftId));
          const data = await res.json();
          setTitle(data.title);
          setDek(data.dek);
          setTag(data.tags?.[0]?.slug || '');
          setBody(data.body);
        } catch (err) {
          console.error('Error loading draft:', err);
        }
      };
      fetchDraft();
    }
  }, [draftId]);

  if (!user) return <Navigate to="/signin" replace />;

  const wordCount = body.trim() ? body.trim().split(/\s+/).length : 0;
  const readMins = Math.max(1, Math.round(wordCount / 200));

  const handleSaveDraft = async () => {
    const payload = { title, dek, body, status: 'draft', tag_ids: tag ? [tag] : [] };
    try {
      const url = draftId ? endpoints.article(draftId) : endpoints.articles;
      const method = draftId ? 'PUT' : 'POST';
      const res = await apiClient(url, {
        method,
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        if (!draftId) {
          navigate(`/write?draft=${data.id}`);
        }
        alert('Draft saved!');
      }
    } catch (err) {
      console.error('Save draft error:', err);
    }
  };

  const handlePublish = async (e) => {
    e.preventDefault();
    if (!title.trim() || !body.trim()) return;
    setLoading(true);
    const payload = { title, dek, body, status: 'published', tag_ids: tag ? [tag] : [] };
    try {
      const url = draftId ? endpoints.article(draftId) : endpoints.articles;
      const method = draftId ? 'PUT' : 'POST';
      const res = await apiClient(url, {
        method,
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setPublished(true);
        setTimeout(() => navigate('/'), 1400);
      }
    } catch (err) {
      console.error('Publish error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="editor container">
      {published ? (
        <div className="editor-published">
          <span className="editor-published-icon">✓</span>
          <h2>Published</h2>
          <p>Your story is live. Taking you back to the feed…</p>
        </div>
      ) : (
        <form onSubmit={handlePublish}>
          <div className="editor-toolbar">
            <span className="eyebrow">{draftId ? 'Editing draft' : 'New story'}</span>
            <div className="editor-toolbar-right">
              <span className="editor-readtime">{wordCount} words · {readMins} min read</span>
              <button type="button" className="btn btn-ghost" onClick={handleSaveDraft}>Save draft</button>
              <button type="submit" className="btn btn-primary" disabled={!title.trim() || !body.trim() || loading}>
                {loading ? 'Publishing...' : 'Publish'}
              </button>
            </div>
          </div>

          <input className="editor-title" placeholder="Title your story" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input className="editor-dek" placeholder="Add a one-line dek (optional)" value={dek} onChange={(e) => setDek(e.target.value)} />

          <div className="editor-tag-row">
            <span>Topic</span>
            <select value={tag} onChange={(e) => setTag(e.target.value)}>
              {tags.map((t) => (
                <option key={t.id} value={t.slug}>{t.name}</option>
              ))}
            </select>
          </div>

          <textarea className="editor-body" placeholder="Write your story…" value={body} onChange={(e) => setBody(e.target.value)} rows={18} />
        </form>
      )}
    </div>
  );
}