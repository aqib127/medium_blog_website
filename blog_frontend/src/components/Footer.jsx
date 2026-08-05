import { Link } from "react-router-dom";
import "../styles/footer.css";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <span className="footer-mark">Blog_Post</span>
        <nav className="footer-links">
          <Link to="/">Home</Link>
          <Link to="/search">Search</Link>
          <Link to="/signin">Sign in</Link>
          <Link to="/signup">Get started</Link>
        </nav>
      </div>
    </footer>
  );
}
