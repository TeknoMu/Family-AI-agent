"""
Voice module - Speech-to-Text (Deepgram) and Text-to-Speech (OpenAI).
Handles transcription of incoming voice messages and generation of voice replies.
"""
import os
import tempfile
import structlog
from app.config import get_settings

logger = structlog.get_logger()


async def transcribe_audio(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    """
    Transcribe audio bytes to text using Deepgram.

    Args:
        audio_bytes: Raw audio file bytes (typically .ogg from Telegram).
        filename: Original filename for format detection.

    Returns:
        Transcribed text, or empty string if transcription fails.
    """
    settings = get_settings()

    if not settings.deepgram_api_key:
        logger.warning("voice_no_deepgram_key", message="DEEPGRAM_API_KEY not set")
        return ""

    try:
        from deepgram import DeepgramClient, PrerecordedOptions

        client = DeepgramClient(settings.deepgram_api_key)

        payload = {"buffer": audio_bytes}

        options = PrerecordedOptions(
            model="nova-2",
            language="it",
            detect_language=True,
            smart_format=True,
            punctuate=True,
        )

        response = client.listen.rest.v("1").transcribe_file(payload, options)

        transcript = response.results.channels[0].alternatives[0].transcript
        detected_lang = response.results.channels[0].detected_language or "unknown"

        logger.info(
            "voice_transcribed",
            language=detected_lang,
            length=len(transcript),
        )

        return transcript

    except Exception as e:
        logger.error("voice_transcribe_error", error=str(e))
        return ""


async def text_to_speech(text: str) -> bytes | None:
    """
    Convert text to speech using OpenAI TTS.

    Args:
        text: The text to convert to speech.

    Returns:
        Audio bytes (mp3 format), or None if generation fails.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        logger.warning("voice_no_openai_key", message="OPENAI_API_KEY not set")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        # Truncate very long responses for TTS (keep under 4096 chars)
        # Strip the disclaimer section for voice (it will be in the text reply)
        tts_text = text
        if "---" in tts_text:
            tts_text = tts_text.split("---")[0].strip()

        if len(tts_text) > 4000:
            tts_text = tts_text[:3950] + "... Per il resto, leggi il messaggio di testo."

        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=tts_text,
            response_format="mp3",
        )

        audio_bytes = response.content

        logger.info("voice_tts_complete", text_length=len(tts_text), audio_size=len(audio_bytes))

        return audio_bytes

    except Exception as e:
        logger.error("voice_tts_error", error=str(e))
        return None
