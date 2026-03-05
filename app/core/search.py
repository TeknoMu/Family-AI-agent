"""
Web search module using Tavily API.
Provides real-time information for all agents, especially news and technology.
"""
import structlog
from app.config import get_settings

logger = structlog.get_logger()


async def search_web(query: str, max_results: int = 5, search_depth: str = "basic") -> str:
    """
    Search the web using Tavily and return formatted results.

    Args:
        query: Search query string.
        max_results: Number of results to return (default 5).
        search_depth: "basic" (fast, free) or "advanced" (deeper, costs more).

    Returns:
        Formatted string of search results ready to inject into agent context.
        Returns empty string if search fails or no API key configured.
    """
    settings = get_settings()

    if not settings.tavily_api_key:
        logger.warning("web_search_no_key", message="TAVILY_API_KEY not set, skipping search")
        return ""

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)

        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=True,
        )

        # Format results for injection into agent context
        parts = []

        # Tavily's AI-generated answer summary
        if response.get("answer"):
            parts.append(f"Summary: {response['answer']}")

        # Individual source results
        for i, result in enumerate(response.get("results", []), 1):
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            parts.append(f"[{i}] {title}\n{content}\nSource: {url}")

        formatted = "\n\n".join(parts)

        logger.info(
            "web_search_complete",
            query=query,
            num_results=len(response.get("results", [])),
        )

        return formatted

    except Exception as e:
        logger.error("web_search_error", query=query, error=str(e))
        return ""


async def search_news(query: str, max_results: int = 5) -> str:
    """
    Search specifically for recent news articles.
    Uses Tavily with news-optimized settings.
    """
    settings = get_settings()

    if not settings.tavily_api_key:
        return ""

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)

        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
            topic="news",
            include_answer=True,
        )

        parts = []
        if response.get("answer"):
            parts.append(f"Latest information: {response['answer']}")

        for i, result in enumerate(response.get("results", []), 1):
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            published = result.get("published_date", "")
            date_str = f" ({published})" if published else ""
            parts.append(f"[{i}] {title}{date_str}\n{content}\nSource: {url}")

        logger.info("news_search_complete", query=query)
        return "\n\n".join(parts)

    except Exception as e:
        logger.error("news_search_error", query=query, error=str(e))
        return ""
