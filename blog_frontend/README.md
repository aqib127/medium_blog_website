# Blog

A personal blogging/publishing platform frontend, built with React + Vite + React Router.

Blog is an original design inspired by long-form reading platforms in general — it uses its
own name, palette, typography, and layout, and is not a copy of any specific company's branding
or copy.

## Features

- **Home feed** — featured "cover story," topic filters, staff-picks and writers-to-follow sidebar
- **Article reader** — a distraction-free reading column with a signature folio/progress rail in the margin, claps, and a comments section
- **Author profiles** — bio, stats, follow button, tabs for stories/about
- **Write / editor** — title, dek, topic, body, live word count -> read-time estimate, publish flow
- **Search** — query + topic-facet filtering across all stories
- **Auth** — sign in / sign up (mocked client-side, persisted to localStorage so your session survives a refresh)

All content (articles, authors, comments) is mock data in `src/data/`, and auth/claps/comments
are handled entirely in the browser — there is no backend. Wire it up to a real API by replacing
the functions in `src/context/AuthContext.jsx` and `src/data/*.js`.

## Getting started

```bash
npm install
npm run dev
```

Then open the printed local URL (usually http://localhost:5173).

## Build for production

```bash
npm run build
npm run preview
```

## Project structure

```
src/
  components/   # Navbar, Footer, ArticleCard, ClapButton, CommentSection, Sidebar
  context/      # AuthContext (mock auth)
  data/         # mock articles.js and users.js
  pages/        # Home, Article, Profile, Write, Search, SignIn, SignUp
  styles/       # variables.css (design tokens) + one stylesheet per component/page
```
