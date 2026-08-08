import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import DraftCard from '../components/DraftCard';
import '../styles/drafts.css';

export default function Drafts() {
  const { user } = useAuth();
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDrafts = async () => {
      if (!user) return;
      try {
        const res = await apiClient(`${endpoints.articles}?status=draft`);
        if (res.ok) {
          const data = await res.json();
          setDrafts(data.results || data);
        }
      } catch (err) {
        console.error('Error fetching drafts:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDrafts();
  }, [user]);

  const handleDelete = async (id) => {
    try {
      const res = await apiClient(endpoints.article(id), { method: 'DELETE' });
      if (res.ok) setDrafts((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error('Error deleting draft:', err);
    }
  };

  if (!user) return <Navigate to="/signin" replace />;

  return (
    <div className="drafts-page">
      <h1>Your Drafts</h1>
      {loading ? (
        <p className="drafts-empty">Loading...</p>
      ) : drafts.length === 0 ? (
        <p className="drafts-empty">You have no saved drafts.</p>
      ) : (
        <ul className="drafts-list">
          {drafts.map((d) => (
            <DraftCard key={d.id} draft={d} onDelete={handleDelete} />
          ))}
        </ul>
      )}
    </div>
  );
}