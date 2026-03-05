"""
Base agent class. All domain agents inherit from this.
"""
from abc import ABC, abstractmethod
import structlog
from app.core.llm import call_llm
from app.core.search import search_web, search_news

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all domain-specific agents."""

    domain: str = ""
    system_prompt: str = ""
    use_web_search: bool = False
    use_news_search: bool = False

    @property
    @abstractmethod
    def disclaimer(self) -> str:
        """Safety disclaimer appended to every response."""
        ...

    def should_search(self, user_message: str) -> bool:
        """Override in subclasses for smarter search decisions."""
        return self.use_web_search or self.use_news_search

    def build_search_query(self, user_message: str) -> str:
        """Build the search query from user message. Override for custom logic."""
        return user_message

    async def respond(self, user_message: str, history: list[dict] | None = None) -> str:
        """
        Generate a response to the user message.
        Optionally enriches context with web search results.

        Args:
            user_message: The user's current message.
            history: Previous messages in the conversation (optional).

        Returns:
            The agent's response text with disclaimer appended.
        """
        messages = []

        # Add conversation history if available (last 10 exchanges max)
        if history:
            messages.extend(history[-20:])  # 20 messages = 10 exchanges

        # Web search enrichment
        search_context = ""
        if self.should_search(user_message):
            query = self.build_search_query(user_message)
            if self.use_news_search:
                search_context = await search_news(query, max_results=5)
            else:
                search_context = await search_web(query, max_results=3)

        # Build the user message with search context
        if search_context:
            enriched_message = (
                f"{user_message}\n\n"
                f"--- Web Search Results ---\n"
                f"{search_context}\n"
                f"--- End Search Results ---\n\n"
                f"Use the search results above to provide accurate, up-to-date information. "
                f"Cite sources when relevant. If the search results conflict, note the disagreement."
            )
        else:
            enriched_message = user_message

        messages.append({"role": "user", "content": enriched_message})

        logger.info(
            "agent_call",
            domain=self.domain,
            searched=bool(search_context),
            message_preview=user_message[:80],
        )

        response = await call_llm(
            messages=messages,
            system=self.system_prompt,
        )

        # Append disclaimer
        full_response = f"{response}\n\n---\n{self.disclaimer}"

        return full_response
