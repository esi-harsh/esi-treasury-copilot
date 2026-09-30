import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

db_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'treasury.db'}")
if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
    rel_path = db_url[len("sqlite:///"):]
    if rel_path.startswith("./") or not Path(rel_path).is_absolute():
        cleaned = rel_path.lstrip("./")
        abs_db_path = (BASE_DIR / cleaned).resolve()
        db_url = f"sqlite:///{abs_db_path.as_posix()}"

DATABASE_URL = db_url
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemini-2.5-flash").strip()
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))


