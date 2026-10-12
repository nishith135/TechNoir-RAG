import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from the project root `.env` file (if present).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# ── Provider Configuration (Decoupled LLM & Embeddings) ──────────
# LLM_PROVIDER: "ollama" (local, free) or "gemini" (cloud)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini" if os.getenv("GEMINI_API_KEY") else "ollama")
# EMBEDDING_PROVIDER: "ollama" (local, free) or "gemini" (cloud)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini" if os.getenv("GEMINI_API_KEY") else "ollama")

# ── Ollama Local Defaults ────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# ── Local-First & Single-User Mode ───────────────────────────────
LOCAL_MODE = os.getenv("LOCAL_MODE", "true").lower() in ("true", "1", "yes")
AUTH_OPTIONAL = os.getenv("AUTH_OPTIONAL", "false").lower() in ("true", "1", "yes")

# ── Gemini (Google LLM & Embeddings) ──────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# ── Embeddings (Google) ─────────────────────
EMBED_MODEL = os.getenv("EMBED_MODEL", "models/gemini-embedding-001")

# ── ChromaDB ─────────────────────────────────────────────────────
CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./chroma_db")

# ── PDF Storage (kept for download/preview) ───────────────────────
PDF_STORE_PATH = os.getenv("PDF_STORE_PATH", "./pdf_store")

# ── Chunking ─────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))
# ── CORS ─────────────────────────────────────────────────────────
_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost")
CORS_ORIGINS = [orig.strip() for orig in _cors_raw.split(",") if orig.strip()]

# ── Upload & Ingestion Limits ─────────────────────────────────────
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))  # 25 MB
MAX_INGEST_PAGES = int(os.getenv("MAX_INGEST_PAGES", "100"))  # 100 pages
# ─────────────────────────────────────────────────────────────────
