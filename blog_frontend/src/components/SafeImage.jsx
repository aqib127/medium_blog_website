import React, { useEffect, useState } from 'react';

const SafeImage = ({ src, alt, className, fallbackColor = '#1F4E4A', style = {} }) => {
  const [imgError, setImgError] = useState(false);

  // FIX: without this, if a component instance is reused for a different
  // article (e.g. list re-ordering) the error flag from a previous image
  // could persist and permanently show the fallback box even though the
  // new src is valid.
  useEffect(() => {
    setImgError(false);
  }, [src]);

  if (!src || imgError) {
    return (
      <div
        className={`safe-image-fallback ${className || ''}`}
        style={{ backgroundColor: fallbackColor, ...style }}
      />
    );
  }

  return (
    <img
      src={src}
      alt={alt || ''}
      className={`safe-image ${className || ''}`}
      style={style}
      onError={() => setImgError(true)}
      loading="lazy"
    />
  );
};

export default SafeImage;