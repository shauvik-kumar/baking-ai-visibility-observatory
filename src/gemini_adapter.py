import time

from google import genai

from config import GEMINI_MODEL


client = genai.Client()


def ask_gemini(question: str):
    start = time.perf_counter()

    try:
        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            input=question,
        )

        latency_ms = int((time.perf_counter() - start) * 1000)

        return {
            "status": "success",
            "latency_ms": latency_ms,
            "text": interaction.output_text,
            "error": None,
            "error_type": None,
        }

    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)

        error_text = str(exc)

        if "429" in error_text or "rate limit" in error_text.lower():
            error_type = "rate_limit"
        else:
            error_type = "api_error"

        return {
            "status": "error",
            "latency_ms": latency_ms,
            "text": "",
            "error": error_text,
            "error_type": error_type,
        }