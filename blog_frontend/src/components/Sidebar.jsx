import React, { useEffect, useState } from 'react';
import { endpoints } from '../config/api';
import apiClient from '../utils/apiClient';

/**
 * FIX: This component used to ignore the props passed by Home.jsx
 * (tags / activeTag / onTagSelect / loading) and instead fetched its own
 * tags and *navigated* to /tag/:slug on click. That meant clicking a tag
 * on the homepage sent the user to TagPage (which has no Sidebar and no
 * active-tag highlight), instead of filtering the feed in place.
 *
 * Now Sidebar is a controlled component: if the parent passes `tags`,
 * `activeTag`, and `onTagSelect`, it uses those directly and simply calls
 * back on click — no navigation, no local refetch, no state duplication.
 * If used standalone without those props, it still works by fetching its
 * own tag list and calling onTagSelect (a no-op fallback logs a warning).
 */
const Sidebar = ({ tags: tagsProp, activeTag = null, onTagSelect, loading: loadingProp }) => {
  const [fetchedTags, setFetchedTags] = useState([]);
  const [fetchLoading, setFetchLoading] = useState(!tagsProp);

  const usingControlledTags = Array.isArray(tagsProp);
  const tags = usingControlledTags ? tagsProp : fetchedTags;
  const loading = usingControlledTags ? !!loadingProp : fetchLoading;

  useEffect(() => {
    if (usingControlledTags) return; // parent is managing tags, nothing to fetch
    const fetchTags = async () => {
      try {
        const res = await apiClient(endpoints.tags);
        if (res.ok) {
          const data = await res.json();
          setFetchedTags(data.results || data);
        }
      } catch (err) {
        console.error('Failed to fetch tags', err);
      } finally {
        setFetchLoading(false);
      }
    };
    fetchTags();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usingControlledTags]);

  const handleTagClick = (slug) => {
    // If the clicked tag is already active, clicking again clears the filter.
    const nextTag = activeTag === slug ? null : slug;
    if (typeof onTagSelect === 'function') {
      onTagSelect(nextTag);
    } else {
      console.warn('Sidebar: no onTagSelect handler provided.');
    }
  };

  return (
    <aside className="feed-sidebar">
      <div>
        <h3 className="text-sm font-bold text-gray-800 mb-4">Browse by topic</h3>
        {loading ? (
          <div className="flex flex-wrap gap-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-8 w-16 bg-gray-200 rounded-full animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="sidebar-button-group">
            {tags.map((tag) => (
              <button
                key={tag.id}
                type="button"
                onClick={() => handleTagClick(tag.slug)}
                aria-pressed={activeTag === tag.slug}
                className="sidebar-tag-button"
              >
                {tag.name}
              </button>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;