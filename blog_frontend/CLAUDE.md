# Frontend — React 19 + Vite (blog_frontend)

React 19, Vite 8, React Router v7, CSS Modules, Quill editor (`react-quill-new`), `date-fns`, `react-loading-skeleton`. No global state library — auth state via React Context.

## Structure (`src/`)
- `components/` — reusable UI: `Navbar`, `ArticleCard`, `Avatar`, `Sidebar`, `Footer`, `ClapButton`, `SaveButton`, `FollowButton`, `CommentSection`, `FollowList`, `DraftCard`, `RelatedArticleCard`, `SafeImage`, `ProtectedRoute`, `Chatbot`/`ChatbotButton`.
- `pages/` — route components: `Home`, `Articles`, `Article`/`ArticleDetail`, `Write`, `Search`, `SignIn`, `SignUp`, `SavedArticles`, `Drafts`, `TagPage`, `ProfileSettings`, and `Profile/` (`Profile`, `ProfileStories`).
- `context/AuthContext.jsx` — global auth state (user, tokens, login/logout).
- `utils/apiClient.js` — the ONLY API layer: fetch wrapper with automatic JWT refresh (queues concurrent 401s to a single refresh request).
- `config/api.js` — centralized `endpoints` map (single source of truth for API URLs).
- `styles/` — CSS modules + `variables.css` (design tokens) + `global.css`.
- `public/` — static assets.

## Conventions
- **API access:** always go through `utils/apiClient.js`, never raw `fetch` (it handles the `Bearer` token + refresh). Endpoints come from `config/api.js` (`import { endpoints } from '../config/api'`). There is no other API wrapper — pages call `apiClient` directly.
- **Auth:** tokens in `localStorage` (`access`/`refresh`). React Router's `ProtectedRoute` guards `/write`, `/saved`, `/drafts`, `/settings`.
- **Images:** use `SafeImage` component for remote/avatar image fallback handling.
- **Loading states:** `react-loading-skeleton` (`Skeleton`) used on list/detail pages.
- **Editor:** Quill via `react-quill-new` in `Write`.
- **Styling:** CSS modules per page/component, one file per concern. Shared tokens in `styles/variables.css`. Match existing naming (`kebab-case` filenames, `.module.css` where used).

## Tooling
- Dev: `npm run dev` (Vite on :5173). Build: `npm run build`. Lint: `npm run lint` (oxlint, config `.oxlintrc.json`).
- `VITE_API_BASE_URL` (`.env`) points to the Django API (`http://127.0.0.1:8000/api/v1/` default).
