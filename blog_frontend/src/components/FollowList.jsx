import { Link } from "react-router-dom";
import Avatar from "./Avatar";
import "../styles/follow-list.css";

export default function FollowList({ users, title }) {
  if (!users || users.length === 0) {
    return <p className="follow-list-empty">No {title.toLowerCase()} yet.</p>;
  }

  return (
    <div className="follow-list">
      <h3>{title}</h3>
      <ul>
        {users.map((u) => (
          <li key={u.id}>
            <Link to={`/@${u.handle}`} className="follow-list-item">
              <Avatar
                name={u.name}
                avatar={u.avatar}
                color={u.avatar_color}
                size={40}
              />
              <div>
                <div className="follow-name">{u.name}</div>
                <div className="follow-handle">@{u.handle}</div>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
