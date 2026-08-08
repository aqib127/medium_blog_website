import { useEffect, useState } from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';
import { useAuth } from '../context/AuthContext';
import ArticleCard from '../components/ArticleCard';
import Avatar from '../components/Avatar';
import FollowList from '../components/FollowList';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import '../styles/profile.css';
import ProfileStories from './Profile/ProfileStories';
import DraftCard from '../components/DraftCard';

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
  const cleanHandle = handle?.replace(/^@/, '') || '';
  const { user } = useAuth();

  const [profileUser, setProfileUser] = useState(null);
  const [stories, setStories] = useState([]);
  const [readingList, setReadingList] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [isFollowedBy, setIsFollowedBy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('stories');

  const [currentUserFollowers, setCurrentUserFollowers] = useState([]);
  const [currentUserFollowing, setCurrentUserFollowing] = useState([]);

  const isOwnProfile = !!(user && profileUser && user.handle === profileUser.handle);

  const fetchAllPages = async (endpoint) => {
    let results = [];
    let nextUrl = endpoint;
    let attempts = 0;
    while (nextUrl && attempts < 20) {
      attempts++;
      try {
        const res = await apiClient(nextUrl, { cache: 'no-store' });
        if (!res.ok) break;
        const data = await res.json();
        const items = data.results || data;
        results = results.concat(items);
        nextUrl = data.next || null;
      } catch (err) {
        console.error('Error in fetchAllPages:', err);
        break;
      }
    }
    return results;
  };

  const fetchProfile = async () => {
    if (!cleanHandle) { setLoading(false); return; }
    setLoading(true);
    try {
      const [userRes, storiesRes, followersData, followingData] = await Promise.all([
        apiClient(endpoints.users(cleanHandle)),
        apiClient(endpoints.userStories(cleanHandle)),
        fetchAllPages(endpoints.userFollowers(cleanHandle)),
        fetchAllPages(endpoints.userFollowing(cleanHandle)),
      ]);

      if (!userRes.ok) throw new Error(`User fetch failed: ${userRes.status}`);

      const userData = await userRes.json();
      const storiesData = storiesRes.ok ? await storiesRes.json() : [];

      setProfileUser(userData);
      setStories(storiesData.results || storiesData);
      setFollowers(followersData);
      setFollowing(followingData);

      if (user) {
        const userFollowsTarget = followersData.some((u) => u.id === user.id);
        const targetFollowsUser = followingData.some((u) => u.id === user.id);
        setIsFollowing(userFollowsTarget);
        setIsFollowedBy(targetFollowsUser);
      } else {
        setIsFollowing(false);
        setIsFollowedBy(false);
      }

      if (user) {
        try {
          const [curFollowers, curFollowing] = await Promise.all([
            fetchAllPages(endpoints.userFollowers(user.handle)),
            fetchAllPages(endpoints.userFollowing(user.handle)),
          ]);
          setCurrentUserFollowers(curFollowers);
          setCurrentUserFollowing(curFollowing);
        } catch (err) {
          console.warn('Could not fetch current user lists:', err);
        }
      } else {
        setCurrentUserFollowers([]);
        setCurrentUserFollowing([]);
      }

      if (user && user.handle === cleanHandle) {
        const [bookmarksRes, draftsRes] = await Promise.all([
          apiClient(endpoints.bookmarks),
          apiClient(`${endpoints.articles}?status=draft`),
        ]);
        const bookmarksData = bookmarksRes.ok ? await bookmarksRes.json() : [];
        const draftsData = draftsRes.ok ? await draftsRes.json() : [];
        const bookmarkList = bookmarksData.results || bookmarksData;
        setReadingList(bookmarkList.map((b) => b.article));
        setDrafts(draftsData.results || draftsData);
      } else {
        setReadingList([]);
        setDrafts([]);
      }
    } catch (err) {
      console.error('Error loading profile:', err);
      setProfileUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProfile(); }, [cleanHandle, user]);
  useEffect(() => { if (tab === 'drafts' && !isOwnProfile) setTab('stories'); }, [isOwnProfile, tab]);

  const handleFollow = async () => {
    if (!user) { window.location.href = '/signin'; return; }
    const method = isFollowing ? 'DELETE' : 'POST';
    const url = endpoints.userFollow(cleanHandle);
    try {
      const response = await apiClient(url, { method });
      if (response.status === 409) { setIsFollowing(true); await fetchProfile(); return; }
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      await fetchProfile();
    } catch (error) { alert(`Failed to update follow status: ${error.message}`); }
  };

  const handleFollowUser = async (targetHandle, currentIsFollowing) => {
    if (!user) { window.location.href = '/signin'; return; }
    const method = currentIsFollowing ? 'DELETE' : 'POST';
    const url = endpoints.userFollow(targetHandle);
    try {
      const response = await apiClient(url, { method });
      if (response.status === 409) { await fetchProfile(); return; }
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      await fetchProfile();
    } catch (error) { alert(`Failed to update follow status: ${error.message}`); }
  };

  const handleDeleteDraft = async (id) => {
    try {
      const res = await apiClient(endpoints.article(id), { method: 'DELETE' });
      if (res.ok) setDrafts((prev) => prev.filter((d) => d.id !== id));
    } catch (err) { console.error('Error deleting draft:', err); }
  };

  if (loading) {
    return (
      <div className="profile-page container">
        <div className="profile-layout">
          <main className="profile-main">
            <h1 className="profile-username"><Skeleton width={200} /></h1>
            <nav className="profile-tabs">
              {TABS.filter(t => !t.ownOnly || true).map(t => (
                <button key={t.key}><Skeleton width={80} /></button>
              ))}
            </nav>
            <div className="profile-tab-panel"><Skeleton count={3} height={100} /></div>
          </main>
          <aside className="profile-sidebar">
            <Skeleton circle width={96} height={96} />
            <Skeleton width={150} height={30} />
            <Skeleton width={100} />
            <Skeleton count={2} />
            <Skeleton width={120} height={36} />
          </aside>
        </div>
      </div>
    );
  }

  if (!profileUser) return <Navigate to="/" replace />;
  const memberSince = profileUser.date_joined ? new Date(profileUser.date_joined).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : null;
  const visibleTabs = TABS.filter((t) => !t.ownOnly || isOwnProfile);
  let buttonLabel = 'Follow';
  if (isFollowing) { buttonLabel = 'Following'; } else if (isFollowedBy) { buttonLabel = 'Follow Back'; }

  const currentUserFollowingIds = currentUserFollowing.map(u => u.id);
  const currentUserFollowersIds = currentUserFollowers.map(u => u.id);
  const followingWithStatus = following.map(u => ({ ...u, isFollowing: currentUserFollowingIds.includes(u.id), isFollowedBy: currentUserFollowersIds.includes(u.id) }));
  const followersWithStatus = followers.map(u => ({ ...u, isFollowing: currentUserFollowingIds.includes(u.id), isFollowedBy: currentUserFollowersIds.includes(u.id) }));

  return (
    <div className="profile-page container">
      <div className="profile-layout">
        <main className="profile-main">
          <h1 className="profile-username">{profileUser.name}</h1>
          <nav className="profile-tabs">
            {visibleTabs.map((t) => (
              <button key={t.key} className={tab === t.key ? 'active' : ''} onClick={() => setTab(t.key)}>
                {t.label}
              </button>
            ))}
          </nav>

          <div className="profile-tab-panel">
            {tab === 'stories' && <ProfileStories stories={stories} />}

            {tab === 'reading-list' && (
              <div className="profile-list">
                {readingList.length ? readingList.map((a) => <ArticleCard key={a.id} article={a} />) : <p className="profile-empty">No saved stories yet.</p>}
              </div>
            )}

            {tab === 'drafts' && isOwnProfile && (
              <div className="profile-drafts-list">
                {drafts.length ? (
                  drafts.map((d) => (
                    <DraftCard key={d.id} draft={d} onDelete={handleDeleteDraft} />
                  ))
                ) : (
                  <p className="profile-empty">You have no saved drafts. <Link to="/write">Start writing</Link></p>
                )}
              </div>
            )}

            {tab === 'followers' && <FollowList users={followersWithStatus} title="Followers" currentUser={user} onFollowToggle={handleFollowUser} profileUserHandle={profileUser.handle} />}
            {tab === 'following' && <FollowList users={followingWithStatus} title="Following" currentUser={user} onFollowToggle={handleFollowUser} profileUserHandle={profileUser.handle} />}
            {tab === 'about' && (
              <div className="profile-about">
                <p>{profileUser.bio || 'This user hasn\u2019t written a bio yet.'}</p>
                {profileUser.location && <p>📍 {profileUser.location}</p>}
                {memberSince && <p>🗓️ Member since {memberSince}</p>}
              </div>
            )}
          </div>
        </main>

        <aside className="profile-sidebar">
          <Avatar name={profileUser.name} avatar={profileUser.avatar} color={profileUser.avatar_color} size={96} />
          <h2 className="profile-sidebar-name">{profileUser.name}</h2>
          <p className="profile-sidebar-handle">@{profileUser.handle}</p>
          {profileUser.bio && <p className="profile-sidebar-bio">{profileUser.bio}</p>}
          <div className="profile-sidebar-stats">
            <button className="profile-stat-btn" onClick={() => setTab('followers')}><strong>{profileUser.followers_count}</strong> Followers</button>
            <span className="dot">·</span>
            <button className="profile-stat-btn" onClick={() => setTab('following')}><strong>{profileUser.following_count}</strong> Following</button>
          </div>
          {isOwnProfile ? (
            <Link to="/settings" className="btn btn-ghost profile-sidebar-action">Edit profile</Link>
          ) : (
            <button className={`btn ${isFollowing ? 'btn-ghost' : 'btn-primary'} profile-sidebar-action`} onClick={handleFollow} id="follow-button-test">{buttonLabel}</button>
          )}
          {(profileUser.twitter || profileUser.github || profileUser.website) && (
            <div className="profile-sidebar-social">
              {profileUser.twitter && <a href={`https://twitter.com/${profileUser.twitter.replace('@', '')}`} target="_blank" rel="noopener noreferrer">🐦 {profileUser.twitter}</a>}
              {profileUser.github && <a href={`https://github.com/${profileUser.github}`} target="_blank" rel="noopener noreferrer">🐙 {profileUser.github}</a>}
              {profileUser.website && <a href={profileUser.website} target="_blank" rel="noopener noreferrer">🔗 {profileUser.website.replace(/^https?:\/\//, '')}</a>}
            </div>
          )}
          {memberSince && <p className="profile-sidebar-since">Member since {memberSince}</p>}
        </aside>
      </div>
    </div>
  );
}