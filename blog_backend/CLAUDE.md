# Backend — Django REST Framework (blog_backend)

Django 4.2 / DRF / SimpleJWT / PostgreSQL. Root of the Django project is `blog_backend/` (contains `manage.py`).

## Layout & settings
- Project settings in `config/settings/`: `base.py` (shared), `development.py`, `production.py`. `config/urls.py` wires `/api/v1/*`.
- Reusable abstractions in `core/`: `BaseModel` (created_at/updated_at), custom permissions, pagination, exceptions.
- `.env` holds secrets/config (DB, JWT lifetimes, CORS, Anthropic key). Never commit real secrets.

## Apps (each under `blog_backend/`)
`core`, `users`, `articles`, `comments`, `bookmarks`, `notifications`, `reading_history`, `reports`, `chatbot`, plus `api/` (legacy url aggregation).

## Conventions
- **Auth:** JWT via SimpleJWT (`Bearer` header). Default DRF permission is `IsAuthenticatedOrReadOnly`.
- **Counters:** denormalized counts (`claps_count`, `comments_count`, `view_count`, `followers_count`, `articles_count`) are stored on the model and updated via Django **signals** (`pre_save`/`post_save`). Keep signals in sync with any new mutating view. Example: `articles/signals.py` recomputes `read_mins` from body word count on `pre_save`.
- **M2M with payload:** `Article.tags` uses a through model `ArticleTag` (explicit through for ordering/payload).
- **Images:** uploaded to `media/` via `upload_to=` (avatars/, article_covers/, article_images/). Debug serves `/media/`.
- **Filtering/search/ordering:** configured globally in `REST_FRAMEWORK` (DjangoFilterBackend, SearchFilter, OrderingFilter) + `PageNumberPagination` (page size 20).
- **Versioning:** URLPathVersioning, `v1`.
- **API schema:** drf-spectacular (`SPECTACULAR_SETTINGS`).
- **Chatbot:** `chatbot/` uses Anthropic API; `USE_MOCK_CHATBOT` env flag swaps in a mock.
- Logging to `logs/django.log` + console.

## Route ordering gotcha
In `articles/urls.py`, custom paths (`articles/tags/`) must be declared **before** the router include, or DRF will treat them as `<int:pk>` lookups. Same principle applies when adding custom sub-routes to other routers.

## Testing
Backend tests live in per-app `tests.py` / `test_*` modules; run with `python manage.py test <app>`.
