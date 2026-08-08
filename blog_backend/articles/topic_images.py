"""
Maps article tags/topics to a topic-consistent cover image instead of one
generic image for every article.

IMPORTANT: We deliberately do NOT use any "keyword -> live stock photo"
redirect service (e.g. the now-shut-down source.unsplash.com, or similar
services like LoremFlickr). Those services are unreliable/unofficial and
break without notice — that's exactly what caused the HTTP 503 errors.

Instead we use https://picsum.photos, the same reliable host your original
seed_existing_article_images.py command already used successfully. Picsum's
/seed/<value>/<w>/<h> endpoint is deterministic: the same seed string always
returns the same photo. We seed by TOPIC KEYWORD (not article id), so every
article about the same topic gets the same distinctive image, and different
topics get different images — satisfying "not one generic image for
everything" without depending on a fragile third-party keyword-search API.

If you want literal, photographically-accurate topic images (a real photo
of Python code for Python articles, etc.), the only correctly-supported way
today is the official Unsplash API (https://api.unsplash.com/search/photos)
with a free Access Key from https://unsplash.com/developers. See
build_unsplash_search_url() below — it's provided but NOT used by default,
since it requires you to add UNSPLASH_ACCESS_KEY to your settings/.env.
"""

import os

# tag/topic name (lowercase) -> (search keywords for Unsplash API, picsum seed)
TOPIC_MAP = {
    # Tags actually present in this project's seed data
    'literature': ('books,literature,library', 'topic-literature'),
    'history': ('history,archive,old-books', 'topic-history'),
    'art': ('art,painting,gallery', 'topic-art'),
    'music': ('music,instrument,concert', 'topic-music'),
    'philosophy': ('philosophy,books,thinking', 'topic-philosophy'),
    'psychology': ('psychology,mind,brain', 'topic-psychology'),
    'programming': ('programming,code,computer', 'topic-programming'),
    'culture': ('culture,people,city', 'topic-culture'),
    'travel': ('travel,landscape,journey', 'topic-travel'),
    'technology': ('technology,computer,workspace', 'topic-technology'),
    'science': ('science,laboratory,research', 'topic-science'),
    'society': ('city,society,architecture', 'topic-society'),
    'craft': ('craftsmanship,handmade,workshop', 'topic-craft'),
    'food': ('food,cooking,kitchen', 'topic-food'),
    'language': ('language,books,writing', 'topic-language'),

    # Common dev-blog tags, kept in case you add these later
    'python': ('python,programming,code', 'topic-python'),
    'javascript': ('javascript,code,web-development', 'topic-javascript'),
    'typescript': ('typescript,code,programming', 'topic-typescript'),
    'react': ('react,frontend,javascript', 'topic-react'),
    'vue': ('vue,frontend,javascript', 'topic-vue'),
    'angular': ('angular,frontend,javascript', 'topic-angular'),
    'django': ('django,python,backend,server', 'topic-django'),
    'flask': ('flask,python,backend', 'topic-flask'),
    'node': ('nodejs,backend,server', 'topic-node'),
    'backend': ('server,backend,code', 'topic-backend'),
    'frontend': ('frontend,web-design,ui', 'topic-frontend'),
    'api': ('api,network,code', 'topic-api'),
    'database': ('database,server,data', 'topic-database'),
    'sql': ('database,sql,data', 'topic-sql'),
    'postgresql': ('database,postgresql,data', 'topic-postgresql'),
    'devops': ('devops,server,cloud', 'topic-devops'),
    'docker': ('docker,containers,server', 'topic-docker'),
    'kubernetes': ('kubernetes,cloud,server', 'topic-kubernetes'),
    'cloud': ('cloud-computing,server,technology', 'topic-cloud'),
    'aws': ('cloud,server,technology', 'topic-aws'),
    'security': ('cybersecurity,security,technology', 'topic-security'),
    'ai': ('artificial-intelligence,technology,robot', 'topic-ai'),
    'machine learning': ('machine-learning,ai,data', 'topic-ml'),
    'ml': ('machine-learning,ai,data', 'topic-ml'),
    'data science': ('data-science,analytics,data', 'topic-data-science'),
    'data': ('data,analytics,charts', 'topic-data'),
    'design': ('design,ui,workspace', 'topic-design'),
    'productivity': ('productivity,workspace,desk', 'topic-productivity'),
    'startup': ('startup,office,team', 'topic-startup'),
    'business': ('business,office,meeting', 'topic-business'),
    'writing': ('writing,typewriter,notebook', 'topic-writing'),
}

DEFAULT_KEYWORDS = 'writing,workspace,desk'
DEFAULT_SEED = 'topic-general'

# Small pool of variations so 10 Python articles aren't all the literal
# identical pixel-for-pixel image, while staying deterministic per article.
VARIATIONS_PER_TOPIC = 4


def _match_topic(tag_names):
    names = [n.strip().lower() for n in (tag_names or []) if n and n.strip()]

    for name in names:
        if name in TOPIC_MAP:
            return TOPIC_MAP[name]

    for name in names:
        for key, value in TOPIC_MAP.items():
            if key in name or name in key:
                return value

    return DEFAULT_KEYWORDS, DEFAULT_SEED


def get_topic_keywords(tag_names):
    """Search keywords, for optional use with the real Unsplash API."""
    keywords, _seed = _match_topic(tag_names)
    return keywords


def build_topic_image_url(article_id, tag_names, width=1200, height=800):
    """
    Reliable default: deterministic Picsum image, seeded by topic (+ a small
    per-article variation bucket so same-topic articles aren't all identical).
    """
    _keywords, seed = _match_topic(tag_names)
    bucket = (article_id or 0) % VARIATIONS_PER_TOPIC
    full_seed = f"{seed}-{bucket}"
    return f"https://picsum.photos/seed/{full_seed}/{width}/{height}"


def build_unsplash_search_url(tag_names, width=1200, height=800):
    """
    OPTIONAL, opt-in: uses the official, currently-supported Unsplash API for
    a literal photographic match to the topic (e.g. a real photo of Python
    code for a Python article). Requires a free Access Key from
    https://unsplash.com/developers set as UNSPLASH_ACCESS_KEY in your
    environment/.env. Returns None if no key is configured, so callers
    should fall back to build_topic_image_url() in that case.
    """
    access_key = os.environ.get('UNSPLASH_ACCESS_KEY', '')
    if not access_key:
        return None
    keywords = get_topic_keywords(tag_names)
    query = keywords.split(',')[0]
    return (
        f"https://api.unsplash.com/photos/random"
        f"?query={query}&orientation=landscape&client_id={access_key}"
    )