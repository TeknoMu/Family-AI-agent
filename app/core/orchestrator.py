"""Orchestrator - routes user messages to the correct domain agent."""
import structlog
from datetime import datetime
from app.core.router import classify_domain
from app.agents.doctor import DoctorAgent
from app.agents.psychologist import PsychologistAgent
from app.agents.science import ScienceAgent
from app.agents.technology import TechnologyAgent
from app.agents.news import NewsAgent

logger = structlog.get_logger()

# Instantiate agents once
AGENTS = {
    "doctor": DoctorAgent(),
    "psychologist": PsychologistAgent(),
    "science": ScienceAgent(),
    "technology": TechnologyAgent(),
    "news": NewsAgent(),
}

# Simple in-memory conversation store (per user)
conversations: dict[str, list[dict]] = {}


def get_date_context() -> str:
    """Return current date string to inject into agent context."""
    now = datetime.now()
    return now.strftime("Today is %A, %B %d, %Y.")


async def handle_message(user_id: str, user_message: str) -> dict:
    """
    Main entry point. Takes a user message, classifies it,
    routes to the right agent, and returns the response.
    """
    # Step 1: Classify the domain
    domain = await classify_domain(user_message)

    # Step 2: Get conversation history for this user
    history = conversations.get(user_id, [])

    # Step 3: Get response from the domain agent (with date context)
    agent = AGENTS[domain]
    date_context = get_date_context()
    enriched_message = date_context + " " + user_message
    response = await agent.respond(enriched_message, history=history)

    # Step 4: Update conversation history (keep last 20 messages)
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append({"role": "user", "content": user_message})
    conversations[user_id].append({"role": "assistant", "content": response})
    conversations[user_id] = conversations[user_id][-20:]

    logger.info("orchestrator_complete", user_id=user_id, domain=domain)

    return {"domain": domain, "response": response}
