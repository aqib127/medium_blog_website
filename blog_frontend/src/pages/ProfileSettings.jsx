import { useState, useEffect, useRef } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { endpoints } from "../config/api";
import apiClient from "../utils/apiClient";
import Avatar from "../components/Avatar";
import "../styles/settings.css";

export default function ProfileSettings() {
  const { user, updateUser } = useAuth();
  const fileInputRef = useRef(null);
  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarColor, setAvatarColor] = useState("#1F4E4A");
  const [avatar, setAvatar] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [twitter, setTwitter] = useState("");
  const [github, setGithub] = useState("");
  const [website, setWebsite] = useState("");
  const [location, setLocation] = useState("");
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setBio(user.bio || "");
      setAvatarColor(user.avatar_color || "#1F4E4A");
      setAvatar(user.avatar || null);
      setAvatarPreview(user.avatar || null);
      setTwitter(user.twitter || "");
      setGithub(user.github || "");
      setWebsite(user.website || "");
      setLocation(user.location || "");
    }
  }, [user]);

  if (!user) return <Navigate to="/signin" replace />;

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      alert("Image size should be less than 2MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      setAvatarPreview(event.target.result);
      setAvatar(file);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveAvatar = async () => {
    setLoading(true);
    try {
      const res = await apiClient(endpoints.userAvatar(user.handle), {
        method: "PATCH",
        body: JSON.stringify({ avatar: null }),
      });
      if (!res.ok) throw new Error("Failed to remove avatar");
      const data = await res.json();
      setAvatarPreview(null);
      setAvatar(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      const updatedUser = { ...user, avatar: null };
      updateUser(updatedUser);
    } catch (err) {
      console.error("Remove avatar error:", err);
      alert("Error removing avatar.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const profileRes = await apiClient(endpoints.userUpdate(user.handle), {
        method: "PUT",
        body: JSON.stringify({
          name,
          bio,
          location,
          twitter,
          github,
          website,
          avatar_color: avatarColor,
        }),
      });
      if (!profileRes.ok) throw new Error("Failed to update profile");
      const updatedUser = await profileRes.json();

      if (avatar && typeof avatar !== "string") {
        const formData = new FormData();
        formData.append("avatar", avatar);
        const avatarRes = await apiClient(endpoints.userAvatar(user.handle), {
          method: "PATCH",
          headers: {},
          body: formData,
        });
        if (avatarRes.ok) {
          const avatarData = await avatarRes.json();
          updatedUser.avatar = avatarData.avatar_url;
        }
      }

      updateUser(updatedUser);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error("Update error:", err);
      alert("Error updating profile.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings-page container">
      <h1>Profile Settings</h1>
      <form onSubmit={handleSubmit} className="settings-form">
        <div className="settings-field settings-avatar-field">
          <label>Profile picture</label>
          <div className="avatar-upload-row">
            <Avatar
              name={name}
              avatar={avatarPreview}
              color={avatarColor}
              size={80}
            />
            <div className="avatar-upload-buttons">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => fileInputRef.current.click()}
              >
                Upload
              </button>
              <input
                type="file"
                ref={fileInputRef}
                accept="image/*"
                onChange={handleAvatarChange}
                style={{ display: "none" }}
              />
              {(avatar || avatarPreview) && (
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={handleRemoveAvatar}
                  disabled={loading}
                >
                  Remove
                </button>
              )}
            </div>
          </div>
          <p className="settings-hint">PNG, JPG up to 2MB</p>
        </div>

        <div className="settings-field">
          <label>Display name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
            required
          />
        </div>

        <div className="settings-field">
          <label>Bio</label>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="Tell us about yourself"
            rows={3}
          />
        </div>

        <div className="settings-field">
          <label>Profile colour</label>
          <div className="color-picker-row">
            <input
              type="color"
              value={avatarColor}
              onChange={(e) => setAvatarColor(e.target.value)}
            />
            <span className="color-hex">{avatarColor}</span>
          </div>
          <p className="settings-hint">
            Used when you don't have a profile picture.
          </p>
        </div>

        <div className="settings-field">
          <label>Location</label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="City, Country"
          />
        </div>

        <div className="settings-field">
          <label>Twitter username</label>
          <input
            type="text"
            value={twitter}
            onChange={(e) => setTwitter(e.target.value)}
            placeholder="@username"
          />
        </div>

        <div className="settings-field">
          <label>GitHub username</label>
          <input
            type="text"
            value={github}
            onChange={(e) => setGithub(e.target.value)}
            placeholder="username"
          />
        </div>

        <div className="settings-field">
          <label>Personal website</label>
          <input
            type="url"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
            placeholder="https://example.com"
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary settings-save"
          disabled={loading}
        >
          {loading ? "Saving..." : "Save changes"}
        </button>
        {saved && <p className="settings-saved">Profile updated!</p>}
      </form>
    </div>
  );
}