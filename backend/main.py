import os
import re
import tempfile
import traceback
import uuid

import chromadb
import google.generativeai as genai
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.config import CHROMA_PERSIST_PATH, GEMINI_API_KEY, GEMINI_MODEL
from backend.ingest import ingest_pdf
from backend.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.retrieval import hybrid_retrieve, _get_cross_encoder
from backend.auth import router as auth_router, get_current_user

# ─── Initialization ────────────────────────────────────────────
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()
app.include_router(auth_router)

# ─── Global error handler ──────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    with open("error.log", "a") as f:
        f.write(f"\nError on {request.method} {request.url}:\n")
        traceback.print_exc(file=f)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {exc}"},
    )

# ─── CORS ──────────────────────────────────────────────────────
origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
allow_origins_list = [o.strip() for o in origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Derive a short, ChromaDB-safe prefix from a user's email."""
    return _sanitize_name(email, max_len=24) or "user"

def _scoped_collection(email: str, display_name: str) -> str:
    """Internal ChromaDB name: {user_prefix}__{display_name} (max 63 chars)."""
    return f"{_user_prefix(email)}__{display_name}"[:63]

def _display_name(email: str, scoped: str) -> str:
    """Strip the user prefix from a scoped collection name."""
    prefix = _user_prefix(email) + "__"
    return scoped[len(prefix):] if scoped.startswith(prefix) else scoped

def _generate_llm_response(prompt: str) -> str:
    """Generate a response from Gemini."""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "LLM returned an empty response."
    except Exception as e:
        return f"LLM error: {e}"

# ─── Endpoints ────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "gemini_configured": bool(GEMINI_API_KEY)}

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

    try:
        tmp_path.write_bytes(await file.read())
        result = ingest_pdf(file_path=str(tmp_path), collection_name=collection_name)
        result["collection"] = display_name  # return display name to frontend
        return result
    finally:
        tmp_path.unlink(missing_ok=True)

@app.post("/query")
async def query(
    req: QueryRequest,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    scoped = _scoped_collection(user["email"], req.collection)
    chunks = hybrid_retrieve(query=req.question, collection_name=scoped, k=req.k)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{build_user_prompt(question=req.question, chunks=chunks)}"
    answer = _generate_llm_response(full_prompt)

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
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
    all_names = [c.name for c in client.list_collections()]
    prefix = _user_prefix(user["email"]) + "__"
    user_names = [_display_name(user["email"], n) for n in all_names if n.startswith(prefix)]
    return {"collections": user_names}
