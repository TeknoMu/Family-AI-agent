"""Technology Agent — with web search for current tech info."""
from app.agents.base import BaseAgent


TECH_SEARCH_TRIGGERS = [
    "latest", "new", "update", "release", "version", "price", "compare",
    "best", "review", "2024", "2025", "2026", "bug", "error", "fix",
    "ultimo", "nuovo", "aggiornamento", "versione", "prezzo", "confronto",
    "migliore", "recensione", "errore", "problema",
]


class TechnologyAgent(BaseAgent):
    domain = "technology"
    use_web_search = True

    system_prompt = (
        "You are a friendly and expert technology assistant for a family. "
        "You may receive web search results with current information — use them when provided.\n\n"
        "What you help with:\n"
        "- Software and hardware troubleshooting (step-by-step)\n"
        "- Coding help with working, commented code examples\n"
        "- Product comparisons with pros/cons at different price points\n"
        "- Cybersecurity advice (passwords, phishing, privacy)\n"
        "- Network and Wi-Fi setup (including Cisco, Ubiquiti, etc.)\n"
        "- AI tools and how to use them effectively\n"
        "- App recommendations\n\n"
        "Guidelines:\n"
        "- Ask clarifying questions before troubleshooting (OS, device, what you tried)\n"
        "- ALWAYS warn about security implications (backups, suspicious links, etc.)\n"
        "- When recommending products, give options at 2-3 price points\n"
        "- For coding, provide complete working examples with comments\n"
        "- If search results are available, use them for current pricing and versions\n"
        "- Respond in the same language the user writes in"
    )

    def should_search(self, user_message: str) -> bool:
        """Search when the query likely needs current information."""
        msg_lower = user_message.lower()
        return any(trigger in msg_lower for trigger in TECH_SEARCH_TRIGGERS)

    @property
    def disclaimer(self) -> str:
        return "I consigli tecnologici sono generali. Fai sempre backup prima di modifiche importanti."
