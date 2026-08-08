import { Link } from "react-router-dom";
import Avatar from "./Avatar";
import "../styles/follow-list.css";

export default function FollowList({ users, title, currentUser, onFollowToggle, profileUserHandle }) {
  if (!users || users.length === 0) {
    return <p className="follow-list-empty">No {title.toLowerCase()} yet.</p>;
  }

  const getButtonLabel = (user) => {
    if (currentUser && user.id === currentUser.id) return null;
    if (user.handle === profileUserHandle) return null;
    if (user.isFollowing) return 'Following';
    if (user.isFollowedBy) return 'Follow Back';
    return 'Follow';
  };

  const handleClick = (user, e) => {
    e.stopPropagation();
    if (!currentUser) {
      window.location.href = '/signin';
      return;
    }
    const label = getButtonLabel(user);
    if (label === null) return;
    const isCurrentlyFollowing = label === 'Following';
    onFollowToggle(user.handle, isCurrentlyFollowing);
  };

  return (
    <div className="follow-list">
      <h3>{title}</h3>
      <ul>
        {users.map((u) => {
          const buttonLabel = getButtonLabel(u);
          return (
            <li key={u.id} className="follow-list-item">
              <Link to={`/@${u.handle}`} className="follow-list-link">
                <Avatar
                  name={u.name}
                  avatar={u.avatar}
                  color={u.avatar_color}
                  size={40}
                />
                <div className="follow-list-info">
                  <div className="follow-name">{u.name}</div>
                  <div className="follow-handle">@{u.handle}</div>
                </div>
              </Link>
              {buttonLabel && (
                <button
                  className={`btn ${buttonLabel === 'Following' ? 'btn-ghost' : 'btn-primary'} follow-list-btn`}
                  onClick={(e) => handleClick(u, e)}
                  disabled={!currentUser}
                >
                  {buttonLabel}
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}