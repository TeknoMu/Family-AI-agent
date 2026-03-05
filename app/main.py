"""Family AI Agent - FastAPI entry point."""
import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.config import get_settings
from app.core.orchestrator import handle_message


structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

app = FastAPI(title="Family AI Agent", version="0.1.0")


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    domain: str
    response: str


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint. Classifies, routes, responds."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    logger.info("chat_request", user_id=request.user_id)
    try:
        result = await handle_message(
            user_id=request.user_id, user_message=request.message
        )
        return ChatResponse(domain=result["domain"], response=result["response"])
    except Exception as e:
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail="Something went wrong.")


@app.on_event("startup")
async def startup():
    settings = get_settings()
    key = settings.anthropic_api_key
    if not key or key == "sk-ant-your-key-here":
        logger.warning("NO_API_KEY", message="Set ANTHROPIC_API_KEY in .env")
    else:
        logger.info("startup", message="Family AI Agent is ready")
