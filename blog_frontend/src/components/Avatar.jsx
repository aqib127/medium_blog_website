import React from "react";

export default function Avatar({
  name,
  avatar = null,
  color = "#1F4E4A",
  size = 32,
  className = "",
  ...props
}) {
  const initials = name
    ? name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "?";

  const style = {
    width: size,
    height: size,
    borderRadius: "50%",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: size * 0.4,
    fontWeight: 600,
    color: "#FAF8F3",
    background: avatar ? "transparent" : color,
    flexShrink: 0,
    overflow: "hidden",
    ...props.style,
  };

  if (avatar) {
    return (
      <img
        src={avatar}
        alt={name || "Avatar"}
        className={`avatar-image ${className}`}
        style={{ ...style, objectFit: "cover" }}
        {...props}
      />
    );
  }

  return (
    <span className={`avatar-initials ${className}`} style={style} {...props}>
      {initials}
    </span>
  );
}