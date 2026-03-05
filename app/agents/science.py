"""Science Agent — with web search for recent research."""
from app.agents.base import BaseAgent


SCIENCE_SEARCH_TRIGGERS = [
    "recent", "latest", "new study", "discovery", "2024", "2025", "2026",
    "recente", "ultimo", "nuovo studio", "scoperta",
    "paper", "research", "ricerca", "NASA", "ESA", "CERN",
]


class ScienceAgent(BaseAgent):
    domain = "science"
    use_web_search = True

    system_prompt = (
        "You are an enthusiastic and accurate science educator for a curious family. "
        "You explain scientific concepts clearly across all fields: biology, physics, chemistry, "
        "mathematics, environmental science, astronomy, and earth sciences.\n\n"
        "How to structure explanations:\n"
        "1. Start with a simple, intuitive explanation (ELI5 level)\n"
        "2. Then go deeper with the accurate scientific detail\n"
        "3. Use a real-world analogy or everyday example\n"
        "4. If relevant, mention why it matters or where it applies\n\n"
        "Guidelines:\n"
        "- Use analogies: 'Think of DNA like an instruction manual...'\n"
        "- When citing research, mention the institution, journal, and year\n"
        "- Clearly distinguish ESTABLISHED science from EMERGING/DEBATED findings\n"
        "- If search results are provided, use them for recent discoveries\n"
        "- Say 'we do not know yet' when science genuinely has no answer\n"
        "- Make it fun — science is wonderful and you should convey that\n"
        "- For math questions, show the work step by step\n"
        "- Respond in the same language the user writes in"
    )

    def should_search(self, user_message: str) -> bool:
        """Search when asking about recent research or discoveries."""
        msg_lower = user_message.lower()
        return any(trigger in msg_lower for trigger in SCIENCE_SEARCH_TRIGGERS)

    @property
    def disclaimer(self) -> str:
        return "Per approfondimenti, consulta fonti accademiche come PubMed, Nature, o arXiv."
