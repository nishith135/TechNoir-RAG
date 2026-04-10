import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List

import chromadb
import requests
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from contextlib import asynccontextmanager

from backend.config import CHROMA_PERSIST_PATH, OLLAMA_BASE_URL, OLLAMA_MODEL
from backend.ingest import ingest_pdf, _get_embed_model
from backend.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.retrieval import hybrid_retrieve, _get_cross_encoder
from backend.evaluate import evaluate_rag
from backend.auth import router as auth_router, get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload models on application startup."""
    print("Preloading embedding models...")
    _get_embed_model()
    _get_cross_encoder()
    print("Models loaded successfully.")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)

# Read CORS origins from env, default to local Vite/React ports for DEV
origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
allow_origins_list = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    collection: str
    k: int = 5


def _get_tmp_dir() -> Path:
    tmp_dir = Path("/tmp")
    try:
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir
    except Exception:
        return Path(tempfile.gettempdir())


def generate_llm_response(prompt: str) -> str:
    """Generate a response from the local Ollama LLM."""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "1h",
            },
            timeout=300,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return "LLM error: Cannot connect to Ollama. Make sure Ollama is running (ollama serve)."
    except requests.exceptions.Timeout:
        return "LLM error: Request timed out (300s). The model may be loading or hardware is slow — try again."
    except Exception as e:
        return f"LLM error: {str(e)}"


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing uploaded filename.")

    filename_lower = file.filename.lower()
    if not filename_lower.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    tmp_dir = _get_tmp_dir()
    suffix = Path(file.filename).suffix.lower()
    tmp_path = tmp_dir / f"{uuid.uuid4().hex}{suffix}"

    collection_name = Path(file.filename).stem

    try:
        data = await file.read()
        tmp_path.write_bytes(data)
        return ingest_pdf(file_path=str(tmp_path), collection_name=collection_name)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass


@app.post("/query")
async def query(req: QueryRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    chunks = hybrid_retrieve(
        query=req.question, collection_name=req.collection, k=req.k)
    user_prompt = build_user_prompt(question=req.question, chunks=chunks)

    # Combine system prompt + user prompt for Ollama (single-turn)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
    answer = generate_llm_response(full_prompt)

    sources: List[Dict[str, Any]] = [
        {"page": int(c.get("page", -1)), "source": c.get("source", ""), "distance": float(c.get("distance", 0.0))}
        for c in chunks
    ]

    return {"answer": answer, "sources": sources}


@app.get("/collections")
async def list_collections(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
    collections = chroma_client.list_collections()
    if collections and isinstance(collections[0], str):
        names = collections
    else:
        names = [c.name for c in collections]
    return {"collections": names}


_TEST_QUESTIONS = [
    "What is the main topic of this document?",
    "What are the key findings or conclusions?",
    "What methodology or approach is described?",
    "Who are the primary authors or contributors mentioned?",
    "What recommendations are provided?",
]


@app.get("/evaluate")
async def evaluate_endpoint(collection: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Run ragas evaluation on hardcoded test questions."""
    scores = evaluate_rag(
        test_questions=_TEST_QUESTIONS,
        collection_name=collection,
    )
    return {"scores": scores, "num_questions": len(_TEST_QUESTIONS)}
