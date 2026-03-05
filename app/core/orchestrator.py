"""Orchestrator - routes user messages to the correct domain agent."""
import structlog
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
# Keys: user_id -> list of {"role": ..., "content": ...}
conversations: dict[str, list[dict]] = {}


async def handle_message(user_id: str, user_message: str) -> dict:
    """
    Main entry point. Takes a user message, classifies it,
    routes to the right agent, and returns the response.

    Returns:
        {"domain": str, "response": str}
    """
    # Step 1: Classify the domain
    domain = await classify_domain(user_message)

    # Step 2: Get conversation history for this user
    history = conversations.get(user_id, [])

    # Step 3: Get response from the domain agent
    agent = AGENTS[domain]
    response = await agent.respond(user_message, history=history)

    # Step 4: Update conversation history (keep last 20 messages)
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append({"role": "user", "content": user_message})
    conversations[user_id].append({"role": "assistant", "content": response})
    conversations[user_id] = conversations[user_id][-20:]

    logger.info("orchestrator_complete", user_id=user_id, domain=domain)

    return {"domain": domain, "response": response}
