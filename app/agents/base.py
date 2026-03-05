"""
Base agent class. All domain agents inherit from this.
"""
from abc import ABC, abstractmethod
import structlog
from app.core.llm import call_llm
from app.core.search import search_web, search_news
from app.core.rag import retrieve_knowledge

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all domain-specific agents."""

    domain: str = ""
    system_prompt: str = ""
    use_web_search: bool = False
    use_news_search: bool = False
    use_rag: bool = False

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
        Enriches context with RAG knowledge and/or web search results.
        """
        messages = []

        # Add conversation history if available (last 10 exchanges max)
        if history:
            messages.extend(history[-20:])

        # RAG knowledge retrieval
        rag_context = ""
        if self.use_rag:
            rag_context = await retrieve_knowledge(
                query=user_message,
                domain=self.domain,
                top_k=5,
            )

        # Web search enrichment
        search_context = ""
        if self.should_search(user_message):
            query = self.build_search_query(user_message)
            if self.use_news_search:
                search_context = await search_news(query, max_results=5)
            else:
                search_context = await search_web(query, max_results=3)

        # Build the enriched message
        parts = [user_message]

        if rag_context:
            parts.append(
                "\n\n--- Knowledge Base ---\n"
                f"{rag_context}\n"
                "--- End Knowledge Base ---"
            )

        if search_context:
            parts.append(
                "\n\n--- Web Search Results ---\n"
                f"{search_context}\n"
                "--- End Search Results ---"
            )

        if rag_context or search_context:
            parts.append(
                "\n\nUse the knowledge base and search results above to provide accurate information. "
                "Prioritize knowledge base content for established guidelines and protocols. "
                "Use web search for current events and recent developments. "
                "Cite sources when relevant."
            )

        enriched_message = "\n".join(parts)
        messages.append({"role": "user", "content": enriched_message})

        logger.info(
            "agent_call",
            domain=self.domain,
            rag=bool(rag_context),
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
