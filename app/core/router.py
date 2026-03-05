"""
Router Agent - classifies each user message into one of 5 domains.
Uses Claude Haiku for speed and minimal cost.
"""
import structlog
from app.core.llm import call_llm
from app.config import get_settings

logger = structlog.get_logger()

DOMAINS = ["doctor", "psychologist", "science", "technology", "news"]

ROUTER_SYSTEM_PROMPT = """You are a domain classifier. Given a user message, classify it into exactly ONE of these domains:

- doctor: Health symptoms, medications, lab results, injuries, diseases, nutrition questions, first aid
- psychologist: Emotions, stress, anxiety, depression, relationships, sleep issues, mental wellness, therapy
- science: Biology, physics, chemistry, math, environment, space, scientific concepts and papers
- technology: Software, hardware, coding, apps, cybersecurity, AI, gadgets, troubleshooting, internet
- news: Current events, politics, elections, economy, world affairs, geopolitics, laws, regulations

Rules:
- Respond with ONLY the domain name, nothing else.
- If the message could fit multiple domains, pick the MOST relevant one.
- If the message is a greeting or unclear, respond with "doctor" as the default (highest priority).
- Never explain your reasoning. Just output one word.
"""


async def classify_domain(user_message: str) -> str:
    """
    Classify a user message into one of the 5 domains.
    Returns one of: doctor, psychologist, science, technology, news
    """
    settings = get_settings()

    response = await call_llm(
        messages=[{"role": "user", "content": user_message}],
        system=ROUTER_SYSTEM_PROMPT,
        model=settings.router_model,
        max_tokens=20,
        temperature=0.0,
    )

    domain = response.strip().lower()

    if domain not in DOMAINS:
        logger.warning("router_unexpected_domain", raw=domain, fallback="doctor")
        domain = "doctor"

    logger.info("router_classified", domain=domain, message_preview=user_message[:80])
    return domain
