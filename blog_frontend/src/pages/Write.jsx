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
    [{ 'list': 'ordered' }, { 'list': 'bullet' }],
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

  const [selectedImage, setSelectedImage] = useState(null);
  const [existingImageUrl, setExistingImageUrl] = useState(null);

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const res = await apiClient(endpoints.tags);
        if (!res.ok) throw new Error('Failed to fetch tags');
        const data = await res.json();
        const tagList = data.results || data;
        setTags(tagList);
        if (tagList.length > 0 && tag === null) {
          setTag(tagList[0].id);
        }
      } catch (err) {
        console.error('Error fetching tags:', err);
        alert('Could not load tags. Please refresh.');
      }
    };
    fetchTags();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
          // Show the already-saved cover image (from the read serializer's
          // image_url) so re-opening a draft doesn't look like the image
          // was lost — it's still there until a new file is chosen.
          setExistingImageUrl(data.image_url || null);
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

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedImage(e.target.files[0]);
    }
  };

  const buildFormData = (status) => {
    const formData = new FormData();
    formData.append('title', title.trim());
    formData.append('dek', dek.trim());
    formData.append('body', body);
    formData.append('status', status);

    // FIX: DRF's ListField reads multipart values via QueryDict.getlist(),
    // so tag ids must be appended as separate form fields — sending
    // JSON.stringify([3]) as one string field fails ListField validation.
    if (tag !== null && tag !== undefined) {
      formData.append('tag_ids', Number(tag));
    }

    // Only attach the image field when a NEW file was picked. If we
    // omit it entirely on update, the backend correctly leaves the
    // existing saved image untouched.
    if (selectedImage) {
      formData.append('image', selectedImage);
    }
    return formData;
  };

  const handleSaveDraft = async () => {
    setSaveMessage('');
    setLoading(true);
    const formData = buildFormData('draft');
    try {
      const url = draftId ? endpoints.article(draftId) : endpoints.articles;
      const method = draftId ? 'PUT' : 'POST';
      const res = await apiClient(url, {
        method,
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setExistingImageUrl(data.image_url || null);
        setSelectedImage(null);
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
    const formData = buildFormData('published');
    try {
      const url = draftId ? endpoints.article(draftId) : endpoints.articles;
      const method = draftId ? 'PUT' : 'POST';
      const res = await apiClient(url, {
        method,
        body: formData,
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
            <span>Cover Image</span>
            <div className="flex items-center gap-2">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="text-sm cursor-pointer"
              />
              {selectedImage ? (
                <div className="flex items-center gap-2 text-xs text-green-600">
                  ✓ {selectedImage.name}
                  <button
                    type="button"
                    className="text-red-500 hover:underline"
                    onClick={() => setSelectedImage(null)}
                  >
                    Remove
                  </button>
                </div>
              ) : existingImageUrl ? (
                <span className="text-xs text-gray-500">Current image set — pick a new file to replace it</span>
              ) : null}
            </div>
          </div>

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