import hashlib
import json
import os
import re
import logging
import tempfile
import uuid

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from backend.config import (
    CHROMA_PERSIST_PATH,
    CORS_ORIGINS,
    EMBEDDING_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    LOCAL_MODE,
    MAX_UPLOAD_BYTES,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    PDF_STORE_PATH,
)
from backend.ingest import ingest_pdf
from backend.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.providers import generate_completion
from backend.retrieval import hybrid_retrieve, _get_cross_encoder
from backend.auth import router as auth_router, get_current_user

# ─── Setup Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Initialization ────────────────────────────────────────────
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API key configured.")

app = FastAPI()
app.include_router(auth_router)

# ─── Global error handler ──────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# ─── Security Headers & CORS ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ─── Schemas ───────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    collection: str
    k: int = 5

# ─── Helpers ──────────────────────────────────────────────────
def _get_tmp_dir() -> Path:
    try:
        tmp = Path(tempfile.gettempdir())
        tmp.mkdir(parents=True, exist_ok=True)
        return tmp
    except Exception:
        return Path(".")

def _sanitize_name(name: str, max_len: int = 40) -> str:
    """Convert an arbitrary string into a ChromaDB-safe name component."""
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    name = re.sub(r"^[^a-zA-Z0-9]+", "", name)
    name = re.sub(r"[^a-zA-Z0-9]+$", "", name)
    return name[:max_len] or "doc"

def _user_prefix(email: str) -> str:
    """Derive a short, collision-free prefix from a user's email."""
    norm = (email or "").strip().lower()
    digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12]
    return f"u_{digest}"

def _scoped_collection(email: str, display_name: str) -> str:
    """Internal ChromaDB name: {user_prefix}__{display_name} (max 63 chars)."""
    clean_display = _sanitize_name(display_name, max_len=45)
    return f"{_user_prefix(email)}__{clean_display}"[:63]

def _display_name(email: str, scoped: str) -> str:
    """Strip the user prefix from a scoped collection name."""
    prefix = _user_prefix(email) + "__"
    return scoped[len(prefix):] if scoped.startswith(prefix) else scoped

def _safe_resolve_path(base_dir: Path, filename: str) -> Path:
    """Ensure resolved file path stays strictly within the target base directory."""
    clean_name = os.path.basename(filename)
    base = base_dir.resolve()
    target = (base / clean_name).resolve()
    if not target.is_relative_to(base):
        raise HTTPException(status_code=400, detail="Invalid path parameter.")
    return target

async def _read_upload_file(file: UploadFile, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
    """Read uploaded file in chunks with strict upper byte size boundary."""
    chunks = []
    total = 0
    chunk_size = 1024 * 1024  # 1 MB
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum allowed size ({max_bytes // (1024 * 1024)}MB).",
            )
        chunks.append(chunk)
    return b"".join(chunks)

def _generate_llm_response(prompt: str) -> str:
    """Generate a response using the decoupled LLM provider (Ollama or Gemini)."""
    return generate_completion(prompt)

# ─── Endpoints ────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "Welcome to the TechNoir RAG API!", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "llm_provider": LLM_PROVIDER,
        "embedding_provider": EMBEDDING_PROVIDER,
        "ollama_base_url": OLLAMA_BASE_URL,
        "ollama_model": OLLAMA_MODEL,
        "gemini_configured": bool(GEMINI_API_KEY),
        "local_mode": LOCAL_MODE,
    }

@app.get("/version")
async def version():
    return {"version": "1.0.0"}

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    safe_filename = os.path.basename(file.filename)
    tmp_path = _get_tmp_dir() / f"{uuid.uuid4().hex}.pdf"

    display_name = _sanitize_name(Path(safe_filename).stem)
    collection_name = _scoped_collection(user["email"], display_name)

    # Persist the PDF for later preview/download
    pdf_store = Path(PDF_STORE_PATH)
    pdf_store.mkdir(parents=True, exist_ok=True)
    stored_pdf_path = _safe_resolve_path(pdf_store, f"{collection_name}.pdf")

    try:
        logger.info(f"Uploading file: {safe_filename} for user: {user['email']}")
        raw_bytes = await _read_upload_file(file)

        # Verify PDF magic byte signature (%PDF-)
        if not raw_bytes.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF document.")

        tmp_path.write_bytes(raw_bytes)
        stored_pdf_path.write_bytes(raw_bytes)

        result = ingest_pdf(file_path=str(tmp_path), collection_name=collection_name)
        result["collection"] = display_name
        logger.info(f"Successfully processed file: {safe_filename}")
        return {
            "chunks_indexed": result.get("chunks_indexed", 0),
            "collection": display_name,
            "source": result.get("source", safe_filename),
            "total_pages": result.get("total_pages", 0),
            "file_size_kb": result.get("file_size_kb", 0),
            "summary": result.get("summary", ""),
            "keywords": result.get("keywords", []),
            "uploaded_at": result.get("uploaded_at", ""),
        }
    except HTTPException:
        stored_pdf_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        stored_pdf_path.unlink(missing_ok=True)
        logger.error(f"Error processing file {safe_filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process and ingest PDF document.")
    finally:
        tmp_path.unlink(missing_ok=True)

@app.post("/query")
async def query(
    req: QueryRequest,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    question_clean = (req.question or "").strip()
    if not question_clean:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(question_clean) > 2000:
        raise HTTPException(status_code=400, detail="Question exceeds 2000 character limit.")

    req_k = max(1, min(req.k, 20))

    try:
        logger.info(f"Querying collection '{req.collection}' for user: {user['email']}")
        scoped = _scoped_collection(user["email"], req.collection)
        chunks = hybrid_retrieve(query=question_clean, collection_name=scoped, k=req_k)
        full_prompt = f"{SYSTEM_PROMPT}\n\n{build_user_prompt(question=question_clean, chunks=chunks)}"
        answer = _generate_llm_response(full_prompt)
        logger.info("Successfully generated query answer.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying collection {req.collection}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to execute query.")

    sources: List[Dict[str, Any]] = [
        {
            "page": int(c.get("page", -1)),
            "source": c.get("source", ""),
            "distance": float(c.get("distance", 0.0)),
        }
        for c in chunks
    ]
    return {"answer": answer, "sources": sources}

@app.get("/collections")
async def list_collections(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    if chromadb is None:
        return {"collections": []}
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
    all_names = [c.name for c in client.list_collections()]
    prefix = _user_prefix(user["email"]) + "__"
    user_names = [_display_name(user["email"], n) for n in all_names if n.startswith(prefix)]
    return {"collections": user_names}

@app.get("/download/{collection}")
async def download_pdf(
    collection: str,
    user: dict = Depends(get_current_user),
):
    """Return the original PDF for a given (display) collection name."""
    scoped = _scoped_collection(user["email"], collection)
    pdf_store = Path(PDF_STORE_PATH)
    pdf_path = _safe_resolve_path(pdf_store, f"{scoped}.pdf")
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found.")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{_sanitize_name(collection)}.pdf",
    )

@app.get("/document-meta")
async def get_document_meta(
    collection: str = Query(..., description="Display collection name"),
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return persisted metadata for a document collection."""
    scoped = _scoped_collection(user["email"], collection)
    meta_path = _safe_resolve_path(Path(CHROMA_PERSIST_PATH), f"{scoped}_meta.json")
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Metadata not found")
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["collection"] = collection
        return meta
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read metadata for {collection}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to read metadata")

@app.get("/chunks")
async def get_chunks(
    collection: str = Query(..., description="Display collection name"),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return raw indexed chunks for a collection (for the Chunk Explorer UI)."""
    scoped = _scoped_collection(user["email"], collection)
    if chromadb is None:
        return {"chunks": []}
    try:
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
        col = client.get_collection(name=scoped)
        result = col.get(limit=limit, include=["documents", "metadatas"])
        chunks = []
        for i, doc in enumerate(result.get("documents") or []):
            meta = (result.get("metadatas") or [])[i] if result.get("metadatas") else {}
            chunks.append({
                "id": (result.get("ids") or [])[i] if result.get("ids") else str(i),
                "text": doc,
                "page": meta.get("page", -1),
                "source": meta.get("source", ""),
            })
        return {"chunks": chunks}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch chunks for {collection}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch chunks")
