import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import '../styles/clap-button.css';

export default function ClapButton({ articleId, initialClaps = 0, userClapped = false }) {
  const { user } = useAuth();
  const [claps, setClaps] = useState(initialClaps);
  const [active, setActive] = useState(false);
  const [isClapped, setIsClapped] = useState(userClapped);
  const [loading, setLoading] = useState(false);

  const handleClap = async () => {
    if (loading) return;
    if (!user) {
      // Redirect to sign-in page if not authenticated
      window.location.href = '/signin';
      return;
    }
    setLoading(true);
    try {
      const res = await apiClient(endpoints.clap(articleId), {
        method: 'POST',
      });
      if (!res.ok) {
        console.error('Clap request failed:', res.status);
        return;
      }
      const data = await res.json();
      setClaps(data.claps_count);
      setIsClapped(data.clapped);
      setActive(true);
      setTimeout(() => setActive(false), 220);
    } catch (err) {
      console.error('Clap error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className={`clap-btn ${isClapped ? 'clap-btn--used' : ''}`}
      onClick={handleClap}
      aria-pressed={isClapped}
      aria-label="Clap for this story"
      disabled={loading}
    >
      <span className={`clap-icon ${active ? 'clap-icon--pop' : ''}`}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path
            d="M7 12.5 3.8 9.3a1.6 1.6 0 1 1 2.26-2.26L9 9.9M11 10.2 8 7.2a1.6 1.6 0 1 1 2.26-2.27L13 7.6M15 9.8l-2.5-2.5a1.6 1.6 0 1 1 2.26-2.27L17.5 7.8M17.5 7.8c1.9 1.9 2.9 3.3 2.9 5.7 0 4.4-3.6 8-8 8h-1.6c-2 0-3.2-.6-4.6-2L3 16.3c-1-1-1-2.6 0-3.6.9-.9 2.3-1 3.4-.2"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span className="clap-count">{claps.toLocaleString()}</span>
    </button>
  );
}