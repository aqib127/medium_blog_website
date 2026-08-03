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
  const [tag, setTag] = useState(null); // will hold tag ID (integer)
  const [body, setBody] = useState('');
  const [tags, setTags] = useState([]);
  const [published, setPublished] = useState(false);
  const [loading, setLoading] = useState(false);

  // Fetch available tags on mount
  useEffect(() => {
    const fetchTags = async () => {
      try {
        const res = await apiClient(endpoints.tags);
        if (!res.ok) throw new Error('Failed to fetch tags');
        const data = await res.json();
        setTags(data);
        if (data.length > 0) {
          setTag(data[0].id); // set default to first tag ID
        }
      } catch (err) {
        console.error('Error fetching tags:', err);
        alert('Could not load tags. Please refresh.');
      }
    };
    fetchTags();
  }, []);

  // Load draft if editing
  useEffect(() => {
    if (draftId) {
      const fetchDraft = async () => {
        try {
          const res = await apiClient(endpoints.article(draftId));
          if (!res.ok) throw new Error('Failed to load draft');
          const data = await res.json();
          setTitle(data.title || '');
          setDek(data.dek || '');
          // Extract tag ID if the article has tags
          if (data.tags && data.tags.length > 0) {
            setTag(data.tags[0].id);
          }
          setBody(data.body || '');
        } catch (err) {
          console.error('Error loading draft:', err);
          alert('Could not load draft.');
        }
      };
      fetchDraft();
    }
  }, [draftId]);

  if (!user) return <Navigate to="/signin" replace />;

  const wordCount = body.trim() ? body.trim().split(/\s+/).length : 0;
  const readMins = Math.max(1, Math.round(wordCount / 200));

  // ---- Helper to build the payload ----
  const buildPayload = (status) => {
    // tag is either an ID (number) or null
    const tagIds = tag !== null && tag !== undefined ? [Number(tag)] : [];
    return {
      title: title.trim(),
      dek: dek.trim(),
      body: body.trim(),
      status: status,
      tag_ids: tagIds,
    };
  };

  // ---- Save Draft ----
  const handleSaveDraft = async () => {
    const payload = buildPayload('draft');
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
          // If new draft, redirect to edit mode with draft ID
          navigate(`/write?draft=${data.id}`);
        } else {
          alert('Draft saved successfully!');
        }
      } else {
        const errorData = await res.json();
        console.error('Save draft error:', errorData);
        alert(`Failed to save draft: ${JSON.stringify(errorData)}`);
      }
    } catch (err) {
      console.error('Save draft error:', err);
      alert('Network error while saving draft.');
    }
  };

  // ---- Publish ----
  const handlePublish = async (e) => {
    e.preventDefault();

    // Validate required fields
    const trimmedTitle = title.trim();
    const trimmedBody = body.trim();
    if (!trimmedTitle) {
      alert('Please enter a title.');
      return;
    }
    if (!trimmedBody) {
      alert('Please write some content.');
      return;
    }

    setLoading(true);
    const payload = buildPayload('published');
    console.log('Publishing payload:', payload); // for debugging

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
      } else {
        const errorData = await res.json();
        console.error('Publish error:', errorData);
        alert(`Failed to publish: ${JSON.stringify(errorData)}`);
      }
    } catch (err) {
      console.error('Publish error:', err);
      alert('Network error while publishing.');
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
              <button type="button" className="btn btn-ghost" onClick={handleSaveDraft}>
                Save draft
              </button>
              <button type="submit" className="btn btn-primary" disabled={loading || !title.trim() || !body.trim()}>
                {loading ? 'Publishing...' : 'Publish'}
              </button>
            </div>
          </div>

          <input
            className="editor-title"
            placeholder="Title your story"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          <input
            className="editor-dek"
            placeholder="Add a one-line dek (optional)"
            value={dek}
            onChange={(e) => setDek(e.target.value)}
          />

          <div className="editor-tag-row">
            <span>Topic</span>
            <select
              value={tag !== null ? tag : ''}
              onChange={(e) => {
                const val = e.target.value;
                setTag(val ? Number(val) : null);
              }}
            >
              {tags.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          <textarea
            className="editor-body"
            placeholder="Write your story…"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={18}
          />
        </form>
      )}
    </div>
  );
}