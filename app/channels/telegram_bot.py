"""Telegram Bot - text and voice message support."""
import io
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.config import get_settings
from app.core.orchestrator import handle_message
from app.core.voice import transcribe_audio, text_to_speech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_MSG_LENGTH = 4000
NEWLINE = "\n"


def is_allowed(uid):
    a = get_settings().allowed_users
    return (not a) or (uid in a)


def split_message(text, max_len=MAX_MSG_LENGTH):
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind(NEWLINE, 0, max_len)
        if split_at == -1:
            split_at = text.rfind(" ", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip(NEWLINE)
    return chunks


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("This bot is private.")
        return
    welcome = (
        "Ciao! Sono il vostro assistente AI familiare.\n\n"
        "Posso rispondere a testo e messaggi vocali!\n\n"
        "Domande su: Salute, Psicologia, Scienza, Tecnologia, Notizie.\n"
        "Scrivimi o inviami un vocale!"
    )
    await update.message.reply_text(welcome)


async def send_response(update, domain, response):
    """Send agent response as text chunks."""
    full_text = "[" + domain + "]\n\n" + response
    for chunk in split_message(full_text):
        await update.message.reply_text(chunk)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    if not is_allowed(update.effective_user.id):
        return
    user_id = str(update.effective_user.id)
    await update.message.chat.send_action("typing")
    try:
        result = await handle_message(user_id=user_id, user_message=update.message.text)
        await send_response(update, result["domain"], result["response"])
    except Exception as ex:
        logger.error("Error: %s", ex, exc_info=True)
        await update.message.reply_text("Mi dispiace, riprova tra poco.")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages: transcribe, process, reply with text + voice."""
    if not is_allowed(update.effective_user.id):
        return
    user_id = str(update.effective_user.id)
    await update.message.chat.send_action("record_voice")

    try:
        # Step 1: Download voice file from Telegram
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        audio_data = await file.download_as_bytearray()
        logger.info("voice_received user=%s duration=%s", user_id, voice.duration)

        # Step 2: Transcribe with Deepgram (auto language detection)
        result = await transcribe_audio(bytes(audio_data))
        transcript = result["text"]
        detected_lang = result["language"]

        if not transcript:
            await update.message.reply_text(
                "Non sono riuscito a capire il vocale. Puoi riprovare o scrivere in testo?"
            )
            return

        # Step 3: Process through agent pipeline
        # Add language hint so the agent responds in the same language
        lang_hint = ""
        if detected_lang and detected_lang.startswith("en"):
            lang_hint = " (Please respond in English, the user spoke in English.)"
        elif detected_lang and detected_lang.startswith("es"):
            lang_hint = " (Please respond in Spanish, the user spoke in Spanish.)"

        agent_result = await handle_message(
            user_id=user_id,
            user_message=transcript + lang_hint,
        )

        # Step 4: Generate voice reply
        audio_reply = await text_to_speech(agent_result["response"])

        if audio_reply:
            # Voice conversation: send voice only
            await update.message.reply_voice(voice=io.BytesIO(audio_reply))
            logger.info("voice_reply_sent user=%s", user_id)
        else:
            # TTS failed: fall back to text
            await send_response(update, agent_result["domain"], agent_result["response"])
            logger.warning("voice_tts_failed, text fallback user=%s", user_id)

    except Exception as ex:
        logger.error("Voice error: %s", ex, exc_info=True)
        await update.message.reply_text("Mi dispiace, riprova tra poco.")


def main():
    token = get_settings().telegram_bot_token
    if not token or "ABCdef" in token:
        print("ERROR: Set TELEGRAM_BOT_TOKEN in .env")
        return
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    print("Bot is running! Text and voice messages supported.")
    application.run_polling()


if __name__ == "__main__":
    main()
