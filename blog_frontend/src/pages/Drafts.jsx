import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import '../styles/drafts.css';

export default function Drafts() {
  const { user } = useAuth();
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    const fetchDrafts = async () => {
      try {
        const res = await apiClient(`${endpoints.articles}?status=draft`);
        const data = await res.json();
        setDrafts(data.results || data);
      } catch (err) {
        console.error('Error fetching drafts:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDrafts();
  }, [user]);

  const deleteDraft = async (id) => {
    try {
      const res = await apiClient(endpoints.article(id), { method: 'DELETE' });
      if (res.ok) {
        setDrafts((prev) => prev.filter((d) => d.id !== id));
      }
    } catch (err) {
      console.error('Error deleting draft:', err);
    }
  };

  if (!user) {
    return (
      <div className="drafts-page container">
        <h1>Your drafts</h1>
        <p className="drafts-empty">Please <a href="/signin">sign in</a> to view your drafts.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="drafts-page container">
        <h1><Skeleton width={200} /></h1>
        {[1,2].map(i => (
          <div key={i} className="draft-item">
            <div><Skeleton count={2} /></div>
            <Skeleton width={60} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="drafts-page container">
      <h1>Your drafts</h1>
      {drafts.length === 0 ? (
        <p className="drafts-empty">You have no saved drafts. <Link to="/write">Start writing</Link></p>
      ) : (
        <ul className="drafts-list">
          {drafts.map((draft) => (
            <li key={draft.id} className="draft-item">
              <Link to={`/write?draft=${draft.id}`} className="draft-link">
                <h3>{draft.title || 'Untitled draft'}</h3>
                <p>{draft.dek || 'No subtitle'}</p>
                <span className="draft-meta">Updated: {new Date(draft.updated_at).toLocaleString()}</span>
              </Link>
              <button className="btn btn-ghost draft-delete" onClick={() => deleteDraft(draft.id)}>Delete</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}