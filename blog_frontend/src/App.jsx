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
import ChatbotButton from "./components/ChatbotButton";
import ProtectedRoute from "./components/ProtectedRoute";
import "./styles/global.css";
import "./styles/chatbot.css";
import Articles from "./pages/Articles";

function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/articles" element={<Articles />} />
        <Route path="/article/:id" element={<Article />} />
        <Route path="/:handle" element={<Profile />} />
        <Route
          path="/write"
          element={
            <ProtectedRoute>
              <Write />
            </ProtectedRoute>
          }
        />
        <Route path="/search" element={<Search />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route
          path="/saved"
          element={
            <ProtectedRoute>
              <SavedArticles />
            </ProtectedRoute>
          }
        />
        <Route
          path="/drafts"
          element={
            <ProtectedRoute>
              <Drafts />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <ProfileSettings />
            </ProtectedRoute>
          }
        />
        <Route path="/tag/:tagName" element={<TagPage />} />
      </Routes>
      <Footer />
      <ChatbotButton />
    </div>
  );
}

export default App;