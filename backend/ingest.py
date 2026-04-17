import json
import os
from datetime import datetime, timezone
from typing import Dict, List

import chromadb
import pdfplumber

from backend.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHROMA_PERSIST_PATH,
    EMBED_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)


import google.generativeai as genai

# Configure GenAI globally (can also be done in main.py)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts using Google Gemini."""
    if not texts:
        return []
    embeddings = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = genai.embed_content(
            model=EMBED_MODEL,
            content=batch,
            task_type="retrieval_document"
        )
        embeddings.extend(result['embedding'])
    return embeddings


def _generate_summary(chunks: List[str]) -> str:
    """Generate a 3-4 sentence summary from the first 3 chunks using Gemini."""
    try:
        context = "\n\n".join(chunks[:3])
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            f"Summarize this document in 3-4 sentences.\n\n{context}"
        )
        return response.text.strip() if response and response.text else ""
    except Exception:
        return ""


def _extract_keywords(chunks: List[str]) -> List[str]:
    """Extract top 8 keyword tags from the first 5 chunks using Gemini."""
    try:
        context = "\n\n".join(chunks[:5])
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            'Return exactly 8 short keyword tags (1-3 words each) that describe the main topics '
            'of this document. Return as a JSON array of strings only, no explanation.'
            f"\n\n{context}"
        )
        if not response or not response.text:
            return []
        raw = response.text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return []


# ── Text chunking ────────────────────────────────────────────────

def _split_recursive_to_tokens(text: str, separators: List[str], chunk_size: int) -> List[str]:
    """
    Recursively split `text` into smaller string tokens using the first separator that applies.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    for sep_idx, sep in enumerate(separators):
        if sep not in text:
            continue

        parts = text.split(sep)
        tokens: List[str] = []

        for part_idx, part in enumerate(parts):
            if part:
                if len(part) <= chunk_size:
                    tokens.append(part)
                else:
                    tokens.extend(
                        _split_recursive_to_tokens(part, separators[sep_idx + 1 :], chunk_size)
                    )

            if part_idx < len(parts) - 1:
                tokens.append(sep)

        return tokens

    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """
    Manual recursive character splitter with overlap.
    """
    separators = ["\n\n", "\n", ". ", " "]

    tokens = _split_recursive_to_tokens(text, separators, chunk_size)
    if not tokens:
        return []

    chunks: List[str] = []
    current = ""

    for token in tokens:
        if not current:
            if len(token) <= chunk_size:
                current = token
            else:
                for i in range(0, len(token), chunk_size):
                    part = token[i : i + chunk_size]
                    if part:
                        chunks.append(part)
                current = ""
            continue

        if len(current) + len(token) <= chunk_size:
            current += token
        else:
            chunks.append(current)
            overlap_text = current[-chunk_overlap:] if chunk_overlap > 0 else ""
            overlap_text = overlap_text[-chunk_size:] if overlap_text else ""
            current = overlap_text + token

            if len(current) > chunk_size:
                current = current[:chunk_size]

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


# ── PDF ingestion ────────────────────────────────────────────────

def ingest_pdf(file_path: str, collection_name: str) -> Dict[str, object]:
    """
    Ingest a PDF into ChromaDB:
      1) Extract page text (keeping page numbers in metadata)
      2) Chunk text with a manual recursive splitter
      3) Embed chunks via Google Gemini
      4) Persist documents + embeddings into ChromaDB
      5) Generate AI summary + keywords via Gemini
      6) Save metadata JSON to ./chroma_db/{collection_name}_meta.json
    """
    source_filename = os.path.basename(file_path)
    file_size_kb = round(os.path.getsize(file_path) / 1024, 1)
    uploaded_at = datetime.now(timezone.utc).isoformat()

    documents: List[str] = []
    metadatas: List[dict] = []
    ids: List[str] = []
    total_pages = 0

    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        global_chunk_idx = 0

        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            if not page_text.strip():
                continue

            page_chunks = _chunk_text(
                page_text,
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
            )

            for local_idx, chunk_text in enumerate(page_chunks):
                documents.append(chunk_text)
                metadatas.append(
                    {
                        "page": page_num,
                        "source": source_filename,
                        "chunk_index": local_idx,
                    }
                )
                ids.append(f"{source_filename}-p{page_num}-{global_chunk_idx}")
                global_chunk_idx += 1

    chunks_indexed = len(documents)

    # Embed and persist to ChromaDB
    embeddings: List[List[float]] = []
    if documents:
        embeddings = _embed_texts(documents)

    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
    collection = chroma_client.get_or_create_collection(name=collection_name)

    if documents:
        if hasattr(collection, "upsert"):
            collection.upsert(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
        else:
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

    # Generate AI-powered summary and keywords from the indexed chunks
    summary = _generate_summary(documents)
    keywords = _extract_keywords(documents)

    # Build and persist metadata JSON
    meta = {
        "collection": collection_name,
        "filename": source_filename,
        "total_pages": total_pages,
        "total_chunks": chunks_indexed,
        "file_size_kb": file_size_kb,
        "uploaded_at": uploaded_at,
        "summary": summary,
        "keywords": keywords,
    }

    meta_dir = os.path.dirname(os.path.abspath(CHROMA_PERSIST_PATH))
    meta_path = os.path.join(meta_dir, "chroma_db", f"{collection_name}_meta.json")
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {
        "chunks_indexed": chunks_indexed,
        "collection": collection_name,
        "source": source_filename,
        "total_pages": total_pages,
        "file_size_kb": file_size_kb,
        "summary": summary,
        "keywords": keywords,
        "uploaded_at": uploaded_at,
    }
