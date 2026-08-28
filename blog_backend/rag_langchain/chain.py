import logging
import re
from django.conf import settings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_ollama import ChatOllama
from .retrieval import retrieve
from .tools import (
    get_top_articles_by_claps,
    get_top_articles_by_comments,
    get_top_articles_by_views,
    get_most_bookmarked_articles,
    get_articles_by_author,
    get_articles_by_tag,
    get_articles_by_tag_partial,
    get_articles_grouped_by_tag,
    get_articles_by_tag_sorted,
    get_articles_by_partial_tag_sorted,
    get_trending_articles,
    get_featured_article,
    get_all_tags,
    get_tag_frequency,
    get_tag_article_count,
    get_tag_total_claps,
    get_tag_total_comments,
    get_tag_total_views,
    get_latest_article_per_tag,
    get_total_users,
    get_total_tags,
    get_website_info,
    get_website_features,
    get_user_profile,
    get_user_followers,
    get_user_following,
    get_follow_count,
    does_user_follow,
    get_bookmarked_articles,
    get_articles_with_min_claps,
    get_articles_with_min_comments,
    get_articles_by_author_and_tag,
    get_latest_article_per_author,
    get_reading_history,
    get_bookmarks_for_user_by_handle,
    get_user_by_handle,
)

logger = logging.getLogger(__name__)

if settings.ANTHROPIC_API_KEY and not settings.USE_MOCK_CHATBOT:
    from langchain_anthropic import ChatAnthropic

GREETINGS = [
    r'^(hi|hello|hey|good morning|good afternoon|good evening|howdy|greetings|hey there|sup|yo|hola)'
]

def is_greeting(text):
    text = text.lower().strip()
    for pattern in GREETINGS:
        if re.match(pattern, text):
            return True
    return False

def format_tool_result(data, title=None):
    if data is None:
        return "No data available."
    if isinstance(data, list):
        if not data:
            return "No results found."
        lines = []
        for idx, item in enumerate(data, 1):
            parts = [f"{idx}. {item.get('title', 'Untitled')}"]
            if 'author' in item and item['author']:
                parts.append(f"by {item['author']}")
            if 'claps' in item:
                parts.append(f"({item['claps']} claps)")
            if 'comments' in item:
                parts.append(f"{item['comments']} comments")
            if 'views' in item:
                parts.append(f"{item['views']} views")
            if 'bookmarks' in item:
                parts.append(f"({item['bookmarks']} bookmarks)")
            if 'handle' in item:
                parts.append(f"(@{item['handle']})")
            lines.append(' '.join(parts))
        result = '\n'.join(lines)
        if title:
            return f"{title}\n{result}"
        return result
    elif isinstance(data, dict):
        if 'title' in data:
            return f"⭐ Featured: {data['title']} by {data.get('author', 'Unknown')}\n{data.get('dek', '')}"
        if 'name' in data:
            return f"{data['name']}\nTotal users: {data['total_users']}\nTotal articles: {data['total_articles']}\nTotal tags: {data['total_tags']}"
        if 'handle' in data:
            return (f"👤 {data['name']} (@{data['handle']})\n"
                    f"Bio: {data.get('bio', '')}\n"
                    f"Followers: {data['followers']}\n"
                    f"Following: {data['following']}\n"
                    f"Articles: {data['articles']}")
    return str(data)

SYSTEM_TEMPLATE = """You are a helpful assistant for a blog website. Answer the user's question using ONLY the provided article content and its metadata. Be concise and factual.

Each article chunk has metadata fields: title, author, tags, claps_count, comments_count. Use these numbers to answer questions like "which articles have the most claps?" – you can compare the numbers across chunks. If the information is not present, say "I don't have enough information."

Context:
{context}
"""

def format_docs(docs):
    if not docs:
        return "No relevant articles found."
    parts = []
    for d in docs:
        meta = d['metadata']
        title = meta.get('title', 'Unknown')
        author = meta.get('author', 'Unknown')
        tags = meta.get('tags', '')
        claps = meta.get('claps_count', 0)
        comments = meta.get('comments_count', 0)
        parts.append(
            f"Title: {title}\n"
            f"Author: {author}\n"
            f"Tags: {tags}\n"
            f"Claps: {claps}\n"
            f"Comments: {comments}\n"
            f"Content: {d['content']}"
        )
    return "\n\n".join(parts)

def get_chat_model():
    if settings.ANTHROPIC_API_KEY and not settings.USE_MOCK_CHATBOT:
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            streaming=True,
            temperature=0.3,
        )
    else:
        return ChatOllama(
            model=settings.OLLAMA_CHAT_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3,
            streaming=True,
        )

def build_rag_chain():
    chat = get_chat_model()
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        ("human", "{question}"),
    ])

    def retrieve_and_format(query):
        docs = retrieve(query)
        logger.info(f"Retrieved {len(docs)} docs for formatting")
        return format_docs(docs)

    chain = (
        {
            "context": RunnableLambda(retrieve_and_format),
            "question": RunnablePassthrough(),
        }
        | prompt
        | chat
        | StrOutputParser()
    )
    return chain

def answer_with_tool(query, user=None):
    q = query.lower().strip()

    # --- 1. Greetings ---
    if is_greeting(query):
        return "Hello! How can I help you today? You can ask me about articles, authors, tags, trending content, and more."

    # --- 2. Website features ---
    if re.search(r'(what can i do|what can you do|features|how to use|functionality)', q):
        features = get_website_features()
        return "📌 You can do the following on this website:\n" + '\n'.join(f"• {f}" for f in features)

    # --- 3. User count ---
    if re.search(r'(how many users|number of users|user count|registered users)', q):
        count = get_total_users()
        return f"There are {count} registered users on this website."

    # --- 4. Tag count ---
    if re.search(r'(how many tags|number of tags|tag count|total tags)', q):
        count = get_total_tags()
        return f"There are {count} tags on this website."

    # --- 5. Website info ---
    if re.search(r'(what is this website about|about this site|tell me about this website)', q):
        info = get_website_info()
        return f"📖 {format_tool_result(info)}"

    # --- 6. Follow relationships ---
    if re.search(r'(how many follow relationships|total follows|follow count)', q):
        count = get_follow_count()
        return f"There are {count} follow relationships on this website."

    # --- 7. Does X follow Y? ---
    if re.search(r'does (.*?) follow (.*?)\?', q):
        m = re.search(r'does (.*?) follow (.*?)\?', q)
        if m and user and user.is_authenticated:
            target_handle = m.group(2).strip()
            result = does_user_follow(target_handle, user)
            if result is None:
                return "You must be logged in to check followers."
            if result:
                return f"Yes, you follow @{target_handle}."
            else:
                return f"No, you do not follow @{target_handle}."
        else:
            return "Please log in to check if you follow someone."

    # --- 8. Tag statistics ---
    # "Which topic has the most articles"
    if re.search(r'which topic has the most articles|topic with most articles|most articles by topic', q):
        data = get_tag_article_count()
        if data:
            top = data[0]
            return f"🏷️ The topic with the most articles is '{top['name']}' with {top['count']} articles."
        return "No tags found."

    # "Which topic has the most likes/claps"
    if re.search(r'which topic has the most (likes|claps|clap)', q):
        data = get_tag_total_claps()
        if data:
            top = data[0]
            return f"🏆 The topic with the most claps is '{top['name']}' with {top['total_claps']} total claps."
        return "No data available."

    # "Which topic has the most comments"
    if re.search(r'which topic has the most comments', q):
        data = get_tag_total_comments()
        if data:
            top = data[0]
            return f"💬 The topic with the most comments is '{top['name']}' with {top['total_comments']} total comments."
        return "No data available."

    # "Which topic has the most views"
    if re.search(r'which topic has the most views', q):
        data = get_tag_total_views()
        if data is None:
            return "Views data is not tracked on this website."
        if data:
            top = data[0]
            return f"👁️ The topic with the most views is '{top['name']}' with {top['total_views']} total views."
        return "No data available."

    # "Latest article per topic"
    if re.search(r'latest article.*(?:from|for) (?:every|each) topic', q):
        data = get_latest_article_per_tag()
        if data:
            lines = [f"• {item['tag']}: {item['title']} by {item['author']} ({item['published_at']})" for item in data]
            return "📰 Latest article per topic:\n" + '\n'.join(lines)
        return "No articles found."

    # "Group articles by tag" (direct database query)
    if re.search(r'(group|organize|list|show).*(articles|content).*(?:by|according to)\s*(?:tag|topic|category)', q) or \
       re.search(r'(all articles|show all)\s*(?:grouped|organized|sorted)\s*by tag', q):
        grouped = get_articles_grouped_by_tag()
        if not grouped:
            return "No articles found."
        lines = []
        for tag, articles in grouped.items():
            lines.append(f"🏷️ **{tag}** ({len(articles)} articles):")
            for art in articles:
                lines.append(f"  • {art['title']} by {art['author']} ({art['claps']} claps)")
            lines.append("")
        return "📚 Articles grouped by tag:\n\n" + '\n'.join(lines)

    # "Most used tag"
    if re.search(r'(which tag.*most frequent|most used tag|popular tag|tag frequency)', q):
        data = get_tag_frequency()
        if data:
            lines = [f"{item['name']} ({item['count']} articles)" for item in data[:5]]
            return f"🏷️ Most used tags:\n" + '\n'.join(lines)
        return "No tags found."

    # "Available tags"
    if re.search(r'(tags|topics|categories) available', q):
        data = get_all_tags()
        return f"🏷️ Available tags: {', '.join(t['name'] for t in data)}"

    # --- 9. Tag-based "most popular" / "latest" ---
    tag_popular_match = re.search(r'(most popular|top|latest|most recent)\s+([a-zA-Z ]+)\s*(articles|stories)', q)
    if tag_popular_match:
        order = tag_popular_match.group(1)
        tag_name = tag_popular_match.group(2).strip()
        sort_by = '-published_at' if 'latest' in order or 'recent' in order else '-claps_count'
        # Exact match
        data = get_articles_by_tag_sorted(tag_name, sort_by, limit=5)
        if data:
            label = "most popular" if 'popular' in order else "latest"
            return f"📄 {label.capitalize()} articles in '{tag_name}':\n{format_tool_result(data)}"
        # Partial match
        data = get_articles_by_partial_tag_sorted(tag_name, sort_by, limit=5)
        if data:
            label = "most popular" if 'popular' in order else "latest"
            return f"📄 {label.capitalize()} articles related to '{tag_name}':\n{format_tool_result(data)}"
        return f"No articles found for '{tag_name}'."

    # --- 10. "Who has written about X?" ---
    who_wrote_match = re.search(r'who has written (?:articles|stories) about\s+([a-zA-Z ]+)', q)
    if who_wrote_match:
        tag_name = who_wrote_match.group(1).strip()
        articles = get_articles_by_partial_tag_sorted(tag_name, sort_by='-claps_count', limit=20)
        if articles:
            authors = set(a['author'] for a in articles)
            if authors:
                return f"✍️ Authors who have written about '{tag_name}': " + ', '.join(authors)
        return f"No authors found for '{tag_name}'."

    # --- 11. General "articles about X" (with sorting) ---
    tag_match = re.search(r'(?:articles|stories).*(?:about|on|with tag)\s+(.+?)(?:\?|$)', q)
    if tag_match:
        tag_query = tag_match.group(1).strip()
        # Exact match
        data_exact = get_articles_by_tag_sorted(tag_query, sort_by='-claps_count', limit=10)
        if data_exact:
            return f"📄 Articles with tag '{tag_query}':\n{format_tool_result(data_exact)}"
        # Partial match
        data_partial = get_articles_by_partial_tag_sorted(tag_query, sort_by='-claps_count', limit=10)
        if data_partial:
            return f"📄 Articles related to '{tag_query}':\n{format_tool_result(data_partial)}"
        return f"No articles found for '{tag_query}'."

    # --- 12. Views ---
    if re.search(r'(most viewed|top views|highest views|views)', q):
        data = get_top_articles_by_views(limit=5)
        if data is None:
            return "Views data is not tracked on this website."
        return f"👁️ Top articles by views:\n{format_tool_result(data)}"

    # --- 13. Reading history ---
    if re.search(r'(my|your) reading history|what (have|did) i read', q):
        history = get_reading_history(user)
        if history is None:
            return "Reading history feature is not available or you need to log in."
        if not history:
            return "You have no reading history yet."
        lines = [f"- {h['article']} (viewed at {h['viewed_at']})" for h in history]
        return "📚 Your reading history:\n" + '\n'.join(lines)

    # --- 14. Bookmarks of a particular user ---
    if re.search(r'bookmarks of|articles bookmarked by\s+([a-zA-Z ]+)', q):
        match = re.search(r'bookmarked by\s+([a-zA-Z ]+)', q)
        if match:
            target_handle = match.group(1).strip()
            target_user = get_user_by_handle(target_handle)
            if not target_user:
                return f"User '{target_handle}' not found."
            bookmarks = get_bookmarks_for_user_by_handle(target_handle, user)
            if bookmarks is None:
                return "You don't have permission to view this user's bookmarks."
            if not bookmarks:
                return f"{target_handle} has no bookmarks."
            return f"📚 Bookmarks of {target_handle}:\n{format_tool_result(bookmarks)}"
        # Fallback: current user's bookmarks
        if user and user.is_authenticated:
            bookmarks = get_bookmarked_articles(user)
            if not bookmarks:
                return "You have no bookmarks."
            return f"📚 Your bookmarks:\n{format_tool_result(bookmarks)}"
        return "Please log in to see your bookmarks."

    # --- 15. Most bookmarked articles ---
    if re.search(r'(most bookmarked|top bookmarks|most saved)', q):
        data = get_most_bookmarked_articles(limit=5)
        return f"📌 Most bookmarked articles:\n{format_tool_result(data)}"

    # --- 16. Claps / likes ---
    if re.search(r'(most|top|highest).*(claps|likes|clap)', q):
        data = get_top_articles_by_claps(limit=5)
        return f"🏆 Top articles by claps:\n{format_tool_result(data)}"

    # --- 17. Articles with min claps ---
    if re.search(r'articles with (?:more than|at least|>=)\s*(\d+)\s*(?:claps|likes)', q):
        m = re.search(r'articles with (?:more than|at least|>=)\s*(\d+)\s*(?:claps|likes)', q)
        if m:
            min_claps = int(m.group(1))
            data = get_articles_with_min_claps(min_claps)
            if data:
                return f"📄 Articles with {min_claps}+ claps:\n{format_tool_result(data)}"
            return f"No articles found with {min_claps}+ claps."

    # --- 18. Articles with min comments ---
    if re.search(r'articles with (?:more than|at least|>=)\s*(\d+)\s*comments', q):
        m = re.search(r'articles with (?:more than|at least|>=)\s*(\d+)\s*comments', q)
        if m:
            min_comments = int(m.group(1))
            data = get_articles_with_min_comments(min_comments)
            if data:
                return f"📄 Articles with {min_comments}+ comments:\n{format_tool_result(data)}"
            return f"No articles found with {min_comments}+ comments."

    # --- 19. Comments (top) ---
    if re.search(r'(most|top).*comments', q):
        data = get_top_articles_by_comments(limit=5)
        return f"💬 Top articles by comments:\n{format_tool_result(data)}"

    # --- 20. Author ---
    author_match = re.search(r'(articles|stories).*(?:by|written by)\s+([a-zA-Z ]+)', q)
    if author_match:
        author_name = author_match.group(2).strip()
        data = get_articles_by_author(author_name)
        return f"📚 Articles by {author_name}:\n{format_tool_result(data)}"

    # --- 21. Combined author+tag ---
    if re.search(r'articles about ([\w\s]+) (?:written|by)\s+([a-zA-Z ]+)', q):
        match = re.search(r'articles about ([\w\s]+) (?:written|by)\s+([a-zA-Z ]+)', q)
        if match:
            tag_name = match.group(1).strip()
            author_name = match.group(2).strip()
            data = get_articles_by_author_and_tag(author_name, tag_name)
            if data:
                return f"📄 Articles about '{tag_name}' by {author_name}:\n{format_tool_result(data)}"
            return f"No articles found about '{tag_name}' by {author_name}."

    # --- 22. Latest article per author ---
    if re.search(r'latest article (?:from|by) each author|latest articles by author', q):
        data = get_latest_article_per_author()
        if data:
            return "📰 Latest article by each author:\n" + format_tool_result(data)
        return "No articles found."

    # --- 23. User profile ---
    if re.search(r'profile of|who is|about user', q):
        handle_match = re.search(r'@([a-zA-Z0-9_-]+)', q)
        if not handle_match:
            handle_match = re.search(r'(?:profile|user)\s+([a-zA-Z]+)', q)
        if handle_match:
            handle = handle_match.group(1)
            profile = get_user_profile(handle)
            if profile:
                return format_tool_result(profile)
            else:
                return f"User @{handle} not found."

    # --- 24. Trending ---
    if re.search(r'trending', q):
        data = get_trending_articles(limit=5)
        return f"🔥 Trending articles:\n{format_tool_result(data)}"

    # --- 25. Featured ---
    if re.search(r'featured', q):
        data = get_featured_article()
        if data:
            return f"⭐ Featured article:\n{format_tool_result(data)}"
        return "No featured article found."

    # --- 26. Fallback: RAG ---
    return None

def answer_stream(query, user=None):
    try:
        result = answer_with_tool(query, user)
        if isinstance(result, str):
            yield result
        else:
            chain = build_rag_chain()
            for chunk in chain.stream(query):
                yield chunk
    except Exception as e:
        logger.exception("Error in answer_stream")
        yield f"Error: {str(e)}"