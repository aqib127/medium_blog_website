import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import '../styles/follow-button.css';

/**
 * Medium-style "Follow" button. Toggles a follow relationship for a given
 * author handle via the existing users/<handle>/follow/ endpoint.
 *
 * `initialFollowing` is optional — when provided (e.g. the article read
 * serializer could expose it in future) we skip the initial lookup.
 * When omitted, the component checks whether the current user already
 * follows the author by inspecting the author's followers list.
 */
export default function FollowButton({ handle, initialFollowing = null, className = '' }) {
  const { user } = useAuth();
  const [isFollowing, setIsFollowing] = useState(!!initialFollowing);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialFollowing !== null) {
      setIsFollowing(initialFollowing);
      return;
    }
    if (!user || !handle) return;
    let cancelled = false;
    const checkFollow = async () => {
      try {
        const res = await apiClient(endpoints.userFollowers(handle));
        if (!res.ok) return;
        const data = await res.json();
        const followers = data.results || data;
        if (!cancelled) setIsFollowing(followers.some((u) => u.id === user.id));
      } catch (err) {
        console.error('Failed to check follow status:', err);
      }
    };
    checkFollow();
    return () => { cancelled = true; };
  }, [handle, user, initialFollowing]);

  const handleFollow = async () => {
    if (!user) {
      window.location.href = '/signin';
      return;
    }
    if (loading) return;
    setLoading(true);
    try {
      const method = isFollowing ? 'DELETE' : 'POST';
      const res = await apiClient(endpoints.userFollow(handle), { method });
      if (res.status === 409) {
        setIsFollowing(true);
        return;
      }
      if (res.ok || res.status === 204) {
        setIsFollowing(!isFollowing);
      } else {
        console.error('Follow request failed:', res.status);
      }
    } catch (err) {
      console.error('Follow error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Defensive: you can't follow yourself — the backend would reject it with
  // a 400 ("You cannot follow yourself."). Render nothing in that case.
  if (user && user.handle === handle) return null;

  return (
    <button
      type="button"
      className={`follow-btn ${isFollowing ? 'follow-btn--following' : ''} ${className}`}
      onClick={handleFollow}
      disabled={loading}
      aria-pressed={isFollowing}
    >
      {isFollowing ? 'Following' : 'Follow'}
    </button>
  );
}
