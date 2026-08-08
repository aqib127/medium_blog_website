# Medium Blog Website — Context Index

Full-stack, Medium-like blogging platform. React (Vite) frontend + Django REST Framework backend + PostgreSQL.

**Always load the relevant sub-doc when working in that area:**
- Backend (Django/DRF): [blog_backend/CLAUDE.md](blog_backend/CLAUDE.md)
- Frontend (React/Vite): [blog_frontend/CLAUDE.md](blog_frontend/CLAUDE.md)
- Articles domain (articles/comments/claps/tags/bookmarks): [blog_backend/articles/CLAUDE.md](blog_backend/articles/CLAUDE.md)
- Auth & users domain (users/profiles/follows): [blog_backend/users/CLAUDE.md](blog_backend/users/CLAUDE.md)

## Architecture at a glance
- `blog_backend/` — Django project. Settings split in `config/settings/` (`base.py`, `development.py`, `production.py`). Custom `AUTH_USER_MODEL = users.User`.
- `blog_frontend/` — React 19 + Vite. React Router v7, CSS modules, Quill editor (`react-quill-new`), no state library (React context + `AuthContext`).
- API base: `/api/v1/`. Versioned via DRF URLPathVersioning (`v1`).

## API routes (backend `config/urls.py`)
- `auth/` → users auth (register, login, refresh, verify, logout, me)
- `users/<handle>/` → profile + stories/followers/following/follow/update/avatar
- `articles/`, `articles/tags/`, `comments/`, `bookmarks/`, `notifications/`, `history/`, `reports/`, `chatbot/`

## Frontend routes (React Router)
`/`, `/articles`, `/article/:id`, `/:handle` (profile), `/write`, `/search`, `/signin`, `/signup`, `/saved`, `/drafts`, `/settings`, `/tag/:tagName`. Protected routes wrap `/write`, `/saved`, `/drafts`, `/settings`.

## How to run
- **Backend:** `cd blog_backend && source venv/bin/activate && python manage.py runserver` (Postgres `blog_db`; see `blog_backend/.env`).
- **Frontend:** `cd blog_frontend && npm run dev` (Vite on :5173, proxies to `VITE_API_BASE_URL`).

## Conventions worth respecting
- Auth = JWT (SimpleJWT) with frontend token-refresh queue in `blog_frontend/src/utils/apiClient.js`; tokens in `localStorage` (`access`/`refresh`).
- Aggregated counters (claps_count, comments_count, followers_count) are denormalized on models and kept in sync via Django signals — update signals, not just the view, when changing counts.
- Django projects are apps under `blog_backend/` (e.g. `core`, `users`, `articles`). Reusable abstractions (base model, permissions, pagination) live in `core/`.
