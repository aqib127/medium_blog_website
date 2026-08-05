import { useState, useEffect } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import ReactQuill from 'react-quill-new';
import 'react-quill-new/dist/quill.snow.css';
import '../styles/write.css';

const modules = {
  toolbar: [
    [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
    ['bold', 'italic', 'underline', 'strike'],
    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
    ['link', 'image', 'blockquote', 'code-block'],
    ['clean'],
  ],
};

const formats = [
  'header',
  'bold', 'italic', 'underline', 'strike',
  'list', 'bullet',
  'link', 'image', 'blockquote', 'code-block',
];

export default function Write() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const draftId = searchParams.get('draft');

  const [title, setTitle] = useState('');
  const [dek, setDek] = useState('');
  const [tag, setTag] = useState(null);
  const [body, setBody] = useState('');
  const [tags, setTags] = useState([]);
  const [published, setPublished] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const res = await apiClient(endpoints.tags);
        if (!res.ok) throw new Error('Failed to fetch tags');
        const data = await res.json();
        setTags(data);
        if (data.length > 0) {
          setTag(data[0].id);
        }
      } catch (err) {
        console.error('Error fetching tags:', err);
        alert('Could not load tags. Please refresh.');
      }
    };
    fetchTags();
  }, []);

  useEffect(() => {
    if (draftId) {
      const fetchDraft = async () => {
        try {
          const res = await apiClient(endpoints.article(draftId));
          if (!res.ok) throw new Error('Failed to load draft');
          const data = await res.json();
          setTitle(data.title || '');
          setDek(data.dek || '');
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

  const wordCount = body.replace(/<[^>]+>/g, '').trim().split(/\s+/).length || 0;
  const readMins = Math.max(1, Math.round(wordCount / 200));

  const buildPayload = (status) => {
    const tagIds = tag !== null && tag !== undefined ? [Number(tag)] : [];
    return {
      title: title.trim(),
      dek: dek.trim(),
      body: body,
      status: status,
      tag_ids: tagIds,
    };
  };

  const handleSaveDraft = async () => {
    setSaveMessage('');
    setLoading(true);
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
          navigate(`/write?draft=${data.id}`);
          setSaveMessage('Draft created! Redirecting...');
        } else {
          setSaveMessage('Draft saved successfully!');
          setTimeout(() => setSaveMessage(''), 3000);
        }
      } else {
        const errorData = await res.json();
        console.error('Save draft error:', errorData);
        alert(`Failed to save draft: ${JSON.stringify(errorData)}`);
      }
    } catch (err) {
      console.error('Save draft error:', err);
      alert('Network error while saving draft.');
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async (e) => {
    e.preventDefault();
    setSaveMessage('');

    const trimmedTitle = title.trim();
    const plainBody = body.replace(/<[^>]+>/g, '').trim();
    if (!trimmedTitle) {
      alert('Please enter a title.');
      return;
    }
    if (!plainBody) {
      alert('Please write some content.');
      return;
    }

    setLoading(true);
    const payload = buildPayload('published');
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
              {saveMessage && <span className="save-message">{saveMessage}</span>}
              <button type="button" className="btn btn-ghost" onClick={handleSaveDraft} disabled={loading}>
                {loading ? 'Saving...' : 'Save draft'}
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

          <ReactQuill
            theme="snow"
            value={body}
            onChange={setBody}
            modules={modules}
            formats={formats}
            placeholder="Write your story…"
            className="editor-body"
          />
        </form>
      )}
    </div>
  );
}