import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./treasury.db")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemini-2.5-flash").strip()
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
