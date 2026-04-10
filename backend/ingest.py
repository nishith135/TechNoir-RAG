import os
from typing import Dict, List

import chromadb
import pdfplumber

from backend.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHROMA_PERSIST_PATH,
    EMBED_MODEL,
)


# ── Local embedding model (lazy-loaded) ──────────────────────────
_embed_model = None


def _get_embed_model():
    """Lazy-load the sentence-transformers embedding model."""
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(EMBED_MODEL)
    return _embed_model


def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts using a local sentence-transformers model."""
    model = _get_embed_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


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
      3) Embed chunks locally via sentence-transformers
      4) Persist documents + embeddings into ChromaDB
    """
    source_filename = os.path.basename(file_path)

    documents: List[str] = []
    metadatas: List[dict] = []
    ids: List[str] = []

    with pdfplumber.open(file_path) as pdf:
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

    if not documents:
        chunks_indexed = 0
    else:
        chunks_indexed = len(documents)

    # Embed locally
    embeddings: List[List[float]] = []
    if documents:
        embeddings = _embed_texts(documents)

    # Persist to Chroma.
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

    return {
        "chunks_indexed": chunks_indexed,
        "collection": collection_name,
        "source": source_filename,
    }
