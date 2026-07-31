import { useEffect, useState } from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import { useAuth } from '../context/AuthContext';
import ArticleCard from '../components/ArticleCard';
import Avatar from '../components/Avatar';
import FollowList from '../components/FollowList';
import '../styles/profile.css';

export default function Profile() {
  const { handle } = useParams();
  const cleanHandle = handle?.replace(/^@/, '');
  const { user } = useAuth();
  const [profileUser, setProfileUser] = useState(null);
  const [stories, setStories] = useState([]);
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('stories');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const [userRes, storiesRes, followersRes, followingRes] = await Promise.all([
          apiClient(endpoints.users(cleanHandle)),
          apiClient(endpoints.userStories(cleanHandle)),
          apiClient(endpoints.userFollowers(cleanHandle)),
          apiClient(endpoints.userFollowing(cleanHandle)),
        ]);
        const userData = await userRes.json();
        const storiesData = storiesRes.ok ? await storiesRes.json() : [];
        const followersData = followersRes.ok ? await followersRes.json() : [];
        const followingData = followingRes.ok ? await followingRes.json() : [];
        setProfileUser(userData);
        setStories(storiesData.results || storiesData);
        setFollowers(followersData.results || followersData);
        setFollowing(followingData.results || followingData);
        // Check if current user follows this profile
        if (user) {
          const isFollower = followingData.some((u) => u.id === user.id);
          setIsFollowing(isFollower);
        }
      } catch (err) {
        console.error('Error loading profile:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [cleanHandle, user]);

  const handleFollow = async () => {
    if (!user) {
      window.location.href = '/signin';
      return;
    }
    try {
      const res = await apiClient(endpoints.userFollow(cleanHandle), {
        method: isFollowing ? 'DELETE' : 'POST',
      });
      if (res.ok) {
        setIsFollowing(!isFollowing);
        setProfileUser((prev) => ({
          ...prev,
          followers_count: isFollowing ? prev.followers_count - 1 : prev.followers_count + 1,
        }));
      }
    } catch (err) {
      console.error('Follow error:', err);
    }
  };

  if (loading) return <div className="loading">Loading profile...</div>;
  if (!profileUser) return <Navigate to="/" replace />;

  const isOwnProfile = user && user.id === profileUser.id;

  return (
    <div className="profile container">
      <header className="profile-header">
        <Avatar name={profileUser.name} avatar={profileUser.avatar} color={profileUser.avatar_color} size={84} />
        <div className="profile-info">
          <h1>{profileUser.name}</h1>
          <p className="profile-handle">@{profileUser.handle}</p>
          <p className="profile-bio">{profileUser.bio}</p>
          <div className="profile-stats">
            <span>{profileUser.followers_count} followers</span>
            <span className="dot">·</span>
            <span>{stories.length} stories</span>
          </div>
        </div>
        <div className="profile-actions">
          {isOwnProfile ? (
            <Link to="/settings" className="btn btn-ghost profile-edit">Edit profile</Link>
          ) : (
            <button
              className={`btn ${isFollowing ? 'btn-ghost' : 'btn-primary'} profile-follow`}
              onClick={handleFollow}
            >
              {isFollowing ? 'Following' : 'Follow'}
            </button>
          )}
        </div>
      </header>

      <nav className="profile-tabs">
        <button className={tab === 'stories' ? 'active' : ''} onClick={() => setTab('stories')}>Stories</button>
        <button className={tab === 'followers' ? 'active' : ''} onClick={() => setTab('followers')}>Followers</button>
        <button className={tab === 'following' ? 'active' : ''} onClick={() => setTab('following')}>Following</button>
        <button className={tab === 'about' ? 'active' : ''} onClick={() => setTab('about')}>About</button>
      </nav>

      {tab === 'stories' && (
        <div className="profile-stories">
          {stories.length ? (
            stories.map((a) => <ArticleCard key={a.id} article={a} />)
          ) : (
            <p className="profile-empty">No stories published yet.</p>
          )}
        </div>
      )}
      {tab === 'followers' && <FollowList users={followers} title="Followers" />}
      {tab === 'following' && <FollowList users={following} title="Following" />}
      {tab === 'about' && (
        <div className="profile-about">
          <p>{profileUser.bio}</p>
          {profileUser.location && <p>📍 {profileUser.location}</p>}
          {profileUser.twitter && <p>🐦 @{profileUser.twitter}</p>}
          {profileUser.github && <p>🐙 {profileUser.github}</p>}
          {profileUser.website && <p>🔗 <a href={profileUser.website} target="_blank" rel="noopener noreferrer">{profileUser.website}</a></p>}
        </div>
      )}
    </div>
  );
}