from __future__ import annotations

from typing import Any, Dict, List

import chromadb
from rank_bm25 import BM25Okapi

from backend.config import CHROMA_PERSIST_PATH, EMBED_MODEL


# ── Local embedding model (lazy-loaded, shared with ingest) ──────
_embed_model = None


def _get_embed_model():
    """Lazy-load the sentence-transformers embedding model."""
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(EMBED_MODEL)
    return _embed_model


def _embed_query(query: str) -> List[float]:
    """Embed a single query using local sentence-transformers model."""
    model = _get_embed_model()
    embedding = model.encode(query, show_progress_bar=False)
    return embedding.tolist()


def retrieve_chunks(query: str, collection_name: str, k: int = 5) -> list[dict]:
    """
    Retrieve the top-k most similar chunks from ChromaDB for the given query.
    """
    if not query or not query.strip():
        return []

    query_embedding = _embed_query(query)

    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
    collection = chroma_client.get_collection(name=collection_name)

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    documents: List[List[str]] = result.get("documents", [])
    metadatas: List[List[Dict[str, Any]]] = result.get("metadatas", [])
    distances: List[List[float]] = result.get("distances", [])

    docs_for_query = documents[0] if documents else []
    metas_for_query = metadatas[0] if metadatas else []
    dists_for_query = distances[0] if distances else []

    chunks: List[dict] = []
    for i, text in enumerate(docs_for_query):
        meta = metas_for_query[i] if i < len(metas_for_query) else {}
        dist = dists_for_query[i] if i < len(dists_for_query) else float("inf")
        chunks.append(
            {
                "text": text,
                "page": int(meta.get("page")) if meta.get("page") is not None else -1,
                "source": str(meta.get("source")) if meta.get("source") is not None else "",
                "distance": float(dist),
            }
        )

    return chunks


def _tokenize_for_bm25(text: str) -> List[str]:
    return [t for t in "".join([c if c.isalnum() else " " for c in text.lower()]).split() if t]


def hybrid_retrieve(query: str, collection_name: str, k: int = 10) -> list[dict]:
    """
    Hybrid retrieval: semantic + BM25 + Reciprocal Rank Fusion.
    """
    if not query or not query.strip():
        return []

    semantic_results = retrieve_chunks(query=query, collection_name=collection_name, k=20)
    if not semantic_results:
        return []

    candidates = semantic_results[:20]
    n = len(candidates)

    corpus_tokens = [_tokenize_for_bm25(c.get("text", "")) for c in candidates]
    query_tokens = _tokenize_for_bm25(query)

    if not any(corpus_tokens) or not query_tokens:
        return candidates[:k]

    bm25 = BM25Okapi(corpus_tokens)
    bm25_scores = bm25.get_scores(query_tokens)

    rank_semantic = list(range(1, n + 1))

    bm25_order = sorted(range(n), key=lambda idx: bm25_scores[idx], reverse=True)
    rank_bm25 = [0] * n
    for pos, idx in enumerate(bm25_order, start=1):
        rank_bm25[idx] = pos

    rrf_scores = []
    for i in range(n):
        score = 1 / (rank_semantic[i] + 60) + 1 / (rank_bm25[i] + 60)
        rrf_scores.append(score)

    top_indices = sorted(range(n), key=lambda i: rrf_scores[i], reverse=True)[:max(k * 2, 10)]
    rrf_top_chunks = [candidates[i] for i in top_indices]

    # Re-score the top chunks using the cross-encoder and return the final top-k
    return rerank(query, rrf_top_chunks, top_n=k)


# ---------------------------------------------------------------------------
# Cross-encoder reranking
# ---------------------------------------------------------------------------

_cross_encoder = None


def _get_cross_encoder():
    """Lazy-load the cross-encoder so startup stays fast."""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder


def rerank(query: str, chunks: list[dict], top_n: int = 5) -> list[dict]:
    """Re-score chunks with a cross-encoder and return top_n."""
    if not chunks:
        return []

    model = _get_cross_encoder()
    pairs = [(query, c.get("text", "")) for c in chunks]
    scores = model.predict(pairs).tolist()

    scored = []
    for chunk, score in zip(chunks, scores):
        entry = {**chunk, "rerank_score": float(score)}
        scored.append(entry)

    scored.sort(key=lambda x: x["rerank_score"], reverse=True)
    return scored[:top_n]
