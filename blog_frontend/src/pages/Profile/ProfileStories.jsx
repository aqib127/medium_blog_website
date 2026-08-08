import React from 'react';
import { Link } from 'react-router-dom';
import SafeImage from '../../components/SafeImage';
import '../../styles/profile.css';

const ProfileStories = ({ stories }) => {
  if (!stories || stories.length === 0) {
    return <p className="profile-empty">No stories published yet.</p>;
  }

  return (
    <div className="profile-stories-list">
      {stories.map((story) => {
        const excerpt =
          story.dek ||
          (story.body ? story.body.replace(/<[^>]+>/g, '').slice(0, 160) + '…' : '');
        const primaryTag = story.tags && story.tags.length > 0 ? story.tags[0].name : null;
        const formattedDate = story.published_at || story.created_at
          ? new Date(story.published_at || story.created_at).toLocaleDateString()
          : '';

        return (
          <div key={story.id} className="profile-story-card">
            {/* Left: story info */}
            <div className="profile-story-body">
              <Link to={`/article/${story.id}`} className="profile-story-link">
                <h3 className="profile-story-title">{story.title}</h3>
                {excerpt && <p className="profile-story-excerpt">{excerpt}</p>}
              </Link>

              <div className="profile-story-meta">
                <div className="profile-story-meta-left">
                  {primaryTag && <span className="profile-story-tag">{primaryTag}</span>}
                  {formattedDate && <span>{formattedDate}</span>}
                  <span>·</span>
                  <span>{story.read_mins || 1} min read</span>
                </div>
                <div className="profile-story-stats">
                  <span>{story.claps_count || 0} 👏</span>
                  <span>{story.comments_count || 0} 💬</span>
                </div>
              </div>
            </div>

            {/* Right: fixed-size, consistent cover thumbnail */}
            <Link to={`/article/${story.id}`} className="profile-story-image-link">
              <SafeImage
                src={story.image_url}
                alt={story.title}
                fallbackColor={story.cover_color || '#1F4E4A'}
              />
            </Link>
          </div>
        );
      })}
    </div>
  );
};

export default ProfileStories;