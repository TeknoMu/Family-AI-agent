"""Telegram Bot - connects your family to the AI agent."""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.config import get_settings
from app.core.orchestrator import handle_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_MSG_LENGTH = 4000  # Telegram limit is 4096, leave margin


def is_allowed(uid):
    a = get_settings().allowed_users
    return (not a) or (uid in a)


def split_message(text, max_len=MAX_MSG_LENGTH):
    """Split long text into chunks that fit Telegram's limit."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to split at a newline
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            # No newline found, split at space
            split_at = text.rfind(" ", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("This bot is private.")
        return
    await update.message.reply_text(
        "Ciao! Sono il vostro assistente AI familiare.\n\n"
        "Domande su: Salute, Psicologia, Scienza, Tecnologia, Notizie.\n"
        "Scrivimi qualsiasi domanda!"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    user_id = str(update.effective_user.id)
    await update.message.chat.send_action("typing")
    try:
        result = await handle_message(user_id=user_id, user_message=update.message.text)
        d = result["domain"]
        r = result["response"]
        full_text = f"[{d}]\n\n{r}"
        for chunk in split_message(full_text):
            await update.message.reply_text(chunk)
    except Exception as ex:
        logger.error("Error: %s", ex, exc_info=True)
        await update.message.reply_text("Mi dispiace, riprova tra poco.")


def main():
    token = get_settings().telegram_bot_token
    if not token or "ABCdef" in token:
        print("ERROR: Set TELEGRAM_BOT_TOKEN in .env")
        return
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    print("Bot is running! Send a message on Telegram.")
    application.run_polling()


if __name__ == "__main__":
    main()
