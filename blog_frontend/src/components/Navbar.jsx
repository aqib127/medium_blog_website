import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Avatar from "./Avatar";
import "../styles/navbar.css";

export default function Navbar() {
  const { user, signOut } = useAuth();
  const [query, setQuery] = useState("");
  const [showMenu, setShowMenu] = useState(false);
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  const handleSignOut = () => {
    signOut();
    setShowMenu(false);
  };

  return (
    <header className="nav">
      <div className="nav-inner container">
        <Link to="/" className="nav-mark">
          Blog_Post
        </Link>

        <form className="nav-search" onSubmit={handleSearch}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            placeholder="Search essays, ideas, writers"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search"
          />
        </form>

        <nav className="nav-actions">
          {user ? (
            <>
              <Link to="/write" className="nav-write">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M12 20h9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  <path
                    d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                Write
              </Link>

              <button
                className="nav-avatar-btn"
                onClick={() => setShowMenu(!showMenu)}
                aria-label="User menu"
              >
                <Avatar
                  name={user.name}
                  avatar={user.avatar}
                  color={user.avatarColor}
                  size={32}
                />
              </button>

              {showMenu && (
                <div className="nav-dropdown">
                  <Link to={`/@${user.handle}`} onClick={() => setShowMenu(false)}>
                    Profile
                  </Link>
                  <Link to="/saved" onClick={() => setShowMenu(false)}>
                    Saved
                  </Link>
                  <Link to="/drafts" onClick={() => setShowMenu(false)}>
                    Drafts
                  </Link>
                  <Link to="/settings" onClick={() => setShowMenu(false)}>
                    Settings
                  </Link>
                  <button className="btn-text nav-signout" onClick={handleSignOut}>
                    Sign out
                  </button>
                </div>
              )}
            </>
          ) : (
            <>
              <Link to="/signin" className="btn-text">
                Sign in
              </Link>
              <Link to="/signup" className="btn btn-primary">
                Get started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}