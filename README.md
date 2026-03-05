# Family AI Agent

A private, multi-domain AI agent system for a family of 3. Provides expert assistance across 5 domains via Telegram (and optionally WhatsApp/voice).

## Domains (priority order)
1. **Human Doctor** — Symptom triage, medication info, lab results (FNOMCeO/AIFA guidelines)
2. **Psychologist** — Emotional support, CBT techniques, crisis detection
3. **Science** — Concepts, papers, biology/physics/chemistry
4. **Technology** — Software/hardware advice, coding help, cybersecurity
5. **News & Politics** — Balanced summaries, fact-checking, multiple viewpoints

## Architecture

```
User (Telegram) → FastAPI Server → Router Agent (Haiku) → Domain Agent (Sonnet) → Response
                                                        ↘ Web Search (Tavily)
                                                        ↘ Evaluation Judge (async)
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/Family-AI-agent.git
cd Family-AI-agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env template and fill in your keys
cp .env.example .env
# Edit .env with your API keys

# 5. Run the server
uvicorn app.main:app --reload --port 8000

# 6. In another terminal, run the Telegram bot
python -m app.channels.telegram_bot
```

## Project Structure

```
Family-AI-agent/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings & env vars
│   ├── core/
│   │   ├── router.py        # Domain classifier (Haiku)
│   │   ├── orchestrator.py  # Routes to the right agent
│   │   └── llm.py           # LLM client wrapper
│   ├── agents/
│   │   ├── base.py          # Base agent class
│   │   ├── doctor.py        # Medical agent
│   │   ├── psychologist.py  # Psychology agent
│   │   ├── science.py       # Science agent
│   │   ├── technology.py    # Technology agent
│   │   └── news.py          # News & politics agent
│   ├── channels/
│   │   └── telegram_bot.py  # Telegram integration
│   └── evaluation/
│       └── judge.py         # Hallucination detection (Phase 4)
├── tests/
│   ├── test_router.py       # Router classification tests
│   └── test_agents.py       # Agent response tests
├── knowledge/               # RAG documents (Phase 2)
├── scripts/
│   └── test_api.py          # Quick manual testing script
├── .env.example             # Template for environment variables
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `TELEGRAM_BOT_TOKEN` | Yes | From @BotFather on Telegram |
| `TAVILY_API_KEY` | No | For web search (news agent) |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING (default: INFO) |

## Development

```bash
# Run tests
pytest tests/ -v

# Run with debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

## Cost Estimate
~€10/month for 5 interactions/day across 3 family members (chat only).

## License
MIT
