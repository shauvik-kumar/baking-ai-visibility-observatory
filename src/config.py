from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "observatory.db"

DATA_DIR.mkdir(exist_ok=True)

GEMINI_MODEL = "gemini-3.6-flash"

API_KEY = os.getenv("GEMINI_API_KEY")


def require_api_key():
    if not API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not loaded. "
            "Load .env before running Gemini."
        )

    return API_KEY