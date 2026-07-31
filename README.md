# Medium Blog Website

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-19-blue)](https://reactjs.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue)](https://www.postgresql.org/)

A full‑stack, Medium‑like blogging platform where users can write, publish, save, and interact with articles. Built with **React (Vite)**, **Django REST Framework**, and **PostgreSQL**.

🌐 **Live Demo:** *[Coming soon]*

---

## ✨ Features

- **🔐 User Authentication** – JWT‑based signup, login, and logout.
- **✍️ Rich Article Editor** – Create, edit, publish, and save drafts.
- **💬 Comments & Replies** – Nested comments with moderation.
- **🔖 Bookmarks & Claps** – Save articles and applaud your favourites.
- **👥 Follow System** – Follow/unfollow other writers.
- **🔍 Search** – Full‑text search with tag filtering.
- **👤 User Profiles** – Edit bio, avatar, and social links.
- **🔔 Notifications** – Real‑time alerts for follows, comments, and claps (backend ready).
- **📖 Reading History** – Track articles you’ve read.
- **📱 Responsive Design** – Works on desktop, tablet, and mobile.

---

## 🛠️ Tech Stack

| Layer          | Technology                                                                 |
|----------------|-----------------------------------------------------------------------------|
| **Frontend**   | React 19, Vite, React Router, CSS Modules                                   |
| **Backend**    | Django 4, Django REST Framework, Simple JWT, Django Filters, drf-spectacular |
| **Database**   | PostgreSQL 18                                                              |
| **File Storage** | Local file system (media/), optional S3 support                           |
| **Server**     | Gunicorn (production), Django development server                           |
| **Other Tools**| Pillow (image processing), python-dotenv, corsheaders                      |

---

## 📁 Project Structure
medium_blog_website/
├── blog_backend/               # Django REST API
│   ├── config/                 # Project settings (base, dev, prod)
│   ├── apps/                   # All Django apps
│   │   ├── core/               # Abstract models, permissions, pagination
│   │   ├── users/              # Custom User, authentication, profiles, follows
│   │   ├── articles/           # Articles, tags, claps, featured, trending
│   │   ├── comments/           # Nested comments
│   │   ├── bookmarks/          # User bookmarks
│   │   ├── notifications/      # In‑app notifications
│   │   ├── reading_history/    # Article view tracking
│   │   └── reports/            # Content reporting
│   ├── media/                  # Uploaded avatars (ignored by Git)
│   ├── requirements/           # Python dependencies (base, dev, prod)
│   ├── manage.py               # Django CLI
│   └── .env                    # Environment variables (ignored)
│
├── blog_frontend/              # React frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components (Navbar, ArticleCard, etc.)
│   │   ├── pages/              # Page components (Home, Article, Profile, Write, etc.)
│   │   ├── context/            # AuthContext (global auth state)
│   │   ├── utils/              # API client with token refresh
│   │   ├── styles/             # CSS modules and global styles
│   │   └── config/             # API endpoint definitions
│   ├── public/                 # Static assets (favicon, icons)
│   ├── package.json            # Node dependencies
│   └── .env                    # Environment variables (ignored)
│
├── .gitignore
├── README.md
├── TODO.md
└── LICENSE                     # (optional)
