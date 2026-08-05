import { useEffect, useState } from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import { useAuth } from '../context/AuthContext';
import ArticleCard from '../components/ArticleCard';
import Avatar from '../components/Avatar';
import FollowList from '../components/FollowList';
import '../styles/profile.css';

const TABS = [
  { key: 'stories', label: 'Stories' },
  { key: 'reading-list', label: 'Reading List' },
  { key: 'drafts', label: 'Drafts', ownOnly: true },
  { key: 'followers', label: 'Followers' },
  { key: 'following', label: 'Following' },
  { key: 'about', label: 'About' },
];

export default function Profile() {
  const { handle } = useParams();
  const cleanHandle = handle?.replace(/^@/, '');
  const { user } = useAuth();

  const [profileUser, setProfileUser] = useState(null);
  const [stories, setStories] = useState([]);
  const [readingList, setReadingList] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('stories');

  const isOwnProfile = !!(user && profileUser && user.handle === profileUser.handle);

  useEffect(() => {
    let cancelled = false;

    const fetchProfile = async () => {
      setLoading(true);
      try {
        const [userRes, storiesRes, followersRes, followingRes] = await Promise.all([
          apiClient(endpoints.users(cleanHandle)),
          apiClient(endpoints.userStories(cleanHandle)),
          apiClient(endpoints.userFollowers(cleanHandle)),
          apiClient(endpoints.userFollowing(cleanHandle)),
        ]);

        if (!userRes.ok) throw new Error('User not found');

        const userData = await userRes.json();
        const storiesData = storiesRes.ok ? await storiesRes.json() : [];
        const followersData = followersRes.ok ? await followersRes.json() : [];
        const followingData = followingRes.ok ? await followingRes.json() : [];

        if (cancelled) return;

        setProfileUser(userData);
        setStories(storiesData.results || storiesData);
        setFollowers(followersData.results || followersData);
        setFollowing(followingData.results || followingData);

        if (user) {
          const followingList = followingData.results || followingData;
          setIsFollowing(followingList.some((u) => u.id === user.id));
        }

        // Reading list (bookmarks) and drafts are private — only fetch
        // them when the viewer IS the profile owner.
        if (user && user.handle === cleanHandle) {
          const [bookmarksRes, draftsRes] = await Promise.all([
            apiClient(endpoints.bookmarks),
            apiClient(`${endpoints.articles}?status=draft`),
          ]);
          const bookmarksData = bookmarksRes.ok ? await bookmarksRes.json() : [];
          const draftsData = draftsRes.ok ? await draftsRes.json() : [];
          if (cancelled) return;
          const bookmarkList = bookmarksData.results || bookmarksData;
          setReadingList(bookmarkList.map((b) => b.article));
          setDrafts(draftsData.results || draftsData);
        } else {
          setReadingList([]);
          setDrafts([]);
        }
      } catch (err) {
        console.error('Error loading profile:', err);
        if (!cancelled) setProfileUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchProfile();
    return () => {
      cancelled = true;
    };
  }, [cleanHandle, user]);

  // If the profile owner changes drafts/tabs, reset to Stories tab so a
  // visitor never gets stuck on a tab that no longer applies to them.
  useEffect(() => {
    if (tab === 'drafts' && !isOwnProfile) setTab('stories');
  }, [isOwnProfile, tab]);

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

  const handleDeleteDraft = async (id) => {
    try {
      const res = await apiClient(endpoints.article(id), { method: 'DELETE' });
      if (res.ok) {
        setDrafts((prev) => prev.filter((d) => d.id !== id));
      }
    } catch (err) {
      console.error('Error deleting draft:', err);
    }
  };

  if (loading) return <div className="loading">Loading profile...</div>;
  if (!profileUser) return <Navigate to="/" replace />;

  const memberSince = profileUser.date_joined
    ? new Date(profileUser.date_joined).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : null;

  const visibleTabs = TABS.filter((t) => !t.ownOnly || isOwnProfile);

  return (
    <div className="profile-page container">
      <div className="profile-layout">
        {/* ---------------- Left content ---------------- */}
        <main className="profile-main">
          <h1 className="profile-username">{profileUser.name}</h1>

          <nav className="profile-tabs">
            {visibleTabs.map((t) => (
              <button
                key={t.key}
                className={tab === t.key ? 'active' : ''}
                onClick={() => setTab(t.key)}
              >
                {t.label}
              </button>
            ))}
          </nav>

          <div className="profile-tab-panel">
            {tab === 'stories' && (
              <div className="profile-list">
                {stories.length ? (
                  stories.map((a) => <ArticleCard key={a.id} article={a} />)
                ) : (
                  <p className="profile-empty">No stories published yet.</p>
                )}
              </div>
            )}

            {tab === 'reading-list' && (
              <div className="profile-list">
                {readingList.length ? (
                  readingList.map((a) => <ArticleCard key={a.id} article={a} />)
                ) : (
                  <p className="profile-empty">No saved stories yet.</p>
                )}
              </div>
            )}

            {tab === 'drafts' && isOwnProfile && (
              <div className="profile-drafts-list">
                {drafts.length ? (
                  drafts.map((d) => (
                    <div key={d.id} className="profile-draft-item">
                      <Link to={`/write?draft=${d.id}`} className="profile-draft-link">
                        <h3>{d.title || 'Untitled draft'}</h3>
                        <p>{d.dek || 'No subtitle'}</p>
                        <span className="profile-draft-meta">
                          Updated {new Date(d.updated_at).toLocaleDateString()}
                        </span>
                      </Link>
                      <button className="btn btn-ghost" onClick={() => handleDeleteDraft(d.id)}>
                        Delete
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="profile-empty">
                    You have no saved drafts. <Link to="/write">Start writing</Link>
                  </p>
                )}
              </div>
            )}

            {tab === 'followers' && <FollowList users={followers} title="Followers" />}
            {tab === 'following' && <FollowList users={following} title="Following" />}

            {tab === 'about' && (
              <div className="profile-about">
                <p>{profileUser.bio || 'This user hasn\u2019t written a bio yet.'}</p>
                {profileUser.location && <p>📍 {profileUser.location}</p>}
                {memberSince && <p>🗓️ Member since {memberSince}</p>}
              </div>
            )}
          </div>
        </main>

        {/* ---------------- Right sidebar ---------------- */}
        <aside className="profile-sidebar">
          <Avatar
            name={profileUser.name}
            avatar={profileUser.avatar}
            color={profileUser.avatar_color}
            size={96}
          />
          <h2 className="profile-sidebar-name">{profileUser.name}</h2>
          <p className="profile-sidebar-handle">@{profileUser.handle}</p>

          {profileUser.bio && <p className="profile-sidebar-bio">{profileUser.bio}</p>}

          <div className="profile-sidebar-stats">
            <button className="profile-stat-btn" onClick={() => setTab('followers')}>
              <strong>{profileUser.followers_count}</strong> Followers
            </button>
            <span className="dot">·</span>
            <button className="profile-stat-btn" onClick={() => setTab('following')}>
              <strong>{profileUser.following_count}</strong> Following
            </button>
          </div>

          {isOwnProfile ? (
            <Link to="/settings" className="btn btn-ghost profile-sidebar-action">
              Edit profile
            </Link>
          ) : (
            <button
              className={`btn ${isFollowing ? 'btn-ghost' : 'btn-primary'} profile-sidebar-action`}
              onClick={handleFollow}
            >
              {isFollowing ? 'Following' : 'Follow'}
            </button>
          )}

          {(profileUser.twitter || profileUser.github || profileUser.website) && (
            <div className="profile-sidebar-social">
              {profileUser.twitter && (
                <a
                  href={`https://twitter.com/${profileUser.twitter.replace('@', '')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  🐦 {profileUser.twitter}
                </a>
              )}
              {profileUser.github && (
                <a
                  href={`https://github.com/${profileUser.github}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  🐙 {profileUser.github}
                </a>
              )}
              {profileUser.website && (
                <a href={profileUser.website} target="_blank" rel="noopener noreferrer">
                  🔗 {profileUser.website.replace(/^https?:\/\//, '')}
                </a>
              )}
            </div>
          )}

          {memberSince && <p className="profile-sidebar-since">Member since {memberSince}</p>}
        </aside>
      </div>
    </div>
  );
}
