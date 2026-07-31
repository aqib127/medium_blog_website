import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Article from "./pages/Article";
import Profile from "./pages/Profile";
import Write from "./pages/Write";
import Search from "./pages/Search";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import SavedArticles from "./pages/SavedArticles";
import Drafts from "./pages/Drafts";
import TagPage from "./pages/TagPage";
import ProfileSettings from "./pages/ProfileSettings";

function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/article/:id" element={<Article />} />
        <Route path="/@:handle" element={<Profile />} />
        <Route path="/write" element={<Write />} />
        <Route path="/search" element={<Search />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/saved" element={<SavedArticles />} />
        <Route path="/drafts" element={<Drafts />} />
        <Route path="/settings" element={<ProfileSettings />} />
        <Route path="/tag/:tagName" element={<TagPage />} />
      </Routes>
      <Footer />
    </div>
  );
}

export default App;