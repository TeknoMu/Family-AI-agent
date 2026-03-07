"""
Voice module - Speech-to-Text (Deepgram) and Text-to-Speech (OpenAI).
"""
import structlog
from app.config import get_settings

logger = structlog.get_logger()


async def transcribe_audio(audio_bytes: bytes) -> dict:
    """
    Transcribe audio bytes to text using Deepgram.

    Returns:
        {"text": str, "language": str} or {"text": "", "language": ""}
    """
    settings = get_settings()

    if not settings.deepgram_api_key:
        logger.warning("voice_no_deepgram_key")
        return {"text": "", "language": ""}

    try:
        from deepgram import DeepgramClient, PrerecordedOptions

        client = DeepgramClient(settings.deepgram_api_key)

        payload = {"buffer": audio_bytes}

        options = PrerecordedOptions(
            model="nova-2",
            detect_language=True,
            smart_format=True,
            punctuate=True,
        )

        response = client.listen.rest.v("1").transcribe_file(payload, options)

        transcript = response.results.channels[0].alternatives[0].transcript
        detected_lang = response.results.channels[0].detected_language or "unknown"

        logger.info("voice_transcribed", language=detected_lang, length=len(transcript))

        return {"text": transcript, "language": detected_lang}

    except Exception as e:
        logger.error("voice_transcribe_error", error=str(e))
        return {"text": "", "language": ""}


async def text_to_speech(text: str) -> bytes | None:
    """
    Convert text to speech using OpenAI TTS.

    Returns:
        Audio bytes (mp3), or None if failed.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        logger.warning("voice_no_openai_key")
        return None

    try:
        import httpx

        # Strip disclaimer for voice (it is in the text reply already)
        tts_text = text
        if "---" in tts_text:
            tts_text = tts_text.split("---")[0].strip()

        # OpenAI TTS has a 4096 char limit
        if len(tts_text) > 4000:
            tts_text = tts_text[:3950] + "... Per il resto, leggi il messaggio di testo."

        if not tts_text:
            logger.warning("voice_tts_empty_text")
            return None

        logger.info("voice_tts_starting", text_length=len(tts_text))

        # Use httpx directly to call OpenAI TTS API for maximum compatibility
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": "Bearer " + settings.openai_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "model": "tts-1",
                    "voice": "nova",
                    "input": tts_text,
                    "response_format": "mp3",
                },
            )

            if response.status_code != 200:
                logger.error(
                    "voice_tts_api_error",
                    status=response.status_code,
                    body=response.text[:500],
                )
                return None

            audio_bytes = response.content
            logger.info("voice_tts_complete", audio_size=len(audio_bytes))
            return audio_bytes

    except Exception as e:
        logger.error("voice_tts_error", error=str(e))
        return None
