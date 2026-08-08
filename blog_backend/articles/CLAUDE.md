# Articles Domain (blog_backend/articles)

Content engine: articles, tags, claps, article images, plus related apps `comments/`, `bookmarks/`. Driven by `ArticleViewSet` + `TagViewSet`.

## Models (`articles/models.py`)
- `Tag` — slug, name, description.
- `Article` — author FK (related_name `articles`), `title`, `dek` (subtitle), `body`, `status` (DRAFT/PUBLISHED), `featured`, `cover_color`, `folio`, denormalized counters (`claps_count`, `comments_count`, `view_count`), `read_mins`, cover `image` (`article_covers/`), `tags` M2M through `ArticleTag`.
- `ArticleTag` — through model for the tags M2M.
- `ArticleImage` — gallery images (`article_images/`), ordered.
- `Clap` — one clap row per user/article (unique together); `claps_count` on Article is the denormalized total.

## Signals
`articles/signals.py` — `pre_save` on `Article` recomputes `read_mins` from `body` word count (`max(1, word_count / 200)`). When adding columns that are derivable from related rows, follow this pattern (recompute in signal) rather than in views.

## URL routes (`articles/urls.py`)
- `articles/` → `ArticleViewSet` (list/retrieve/create/update/delete/clap)
- `articles/featured/`, `articles/trending/`
- `articles/tags/` → `TagViewSet.list` (custom route — must stay before router include)
- `articles/<id>/clap/`

## Related apps
- `comments/` — nested comments; `Comment.parent` self-FK for replies; `Comment.article` FK (related_name `comments`). Mutations must keep `Article.comments_count` in sync via signals.
- `bookmarks/` — save/un-save an article for a user.

## Frontend counterpart
Endpoints in `blog_frontend/src/config/api.js` (`articles`, `clap`, `featured`, `trending`, `tagArticles`). Components: `ArticleCard`, `ClapButton`, `SaveButton`, `CommentSection`, `RelatedArticleCard`.
