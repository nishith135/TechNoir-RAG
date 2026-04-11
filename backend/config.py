import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from the project root `.env` file (if present).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# ── Gemini (Google LLM & Embeddings) ──────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# ── Embeddings (Google) ─────────────────────
EMBED_MODEL = os.getenv("EMBED_MODEL", "models/gemini-embedding-001")

# ── ChromaDB ─────────────────────────────────────────────────────
CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./chroma_db")

# ── Chunking ─────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))
# ─────────────────────────────────────────────────────────────────
