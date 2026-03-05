"""
Thin wrapper around the Anthropic API client.
Centralises model calls so we can add logging, retries, and fallback later.
"""
import anthropic
import structlog
from app.config import get_settings

logger = structlog.get_logger()


def get_client() -> anthropic.Anthropic:
    """Return a reusable Anthropic client."""
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key)


async def call_llm(
    messages: list[dict],
    system: str = "",
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    """
    Send a message to Claude and return the text response.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."} dicts.
        system: System prompt.
        model: Model ID override. Defaults to agent_model from settings.
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature (lower = more deterministic).

    Returns:
        The assistant's text response.
    """
    settings = get_settings()
    model = model or settings.agent_model
    client = get_client()

    logger.info("llm_call", model=model, message_count=len(messages))

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        text = response.content[0].text
        logger.info(
            "llm_response",
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return text

    except anthropic.APIError as e:
        logger.error("llm_error", model=model, error=str(e))
        raise
