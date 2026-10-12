import json
import logging
import os
from typing import List, Optional
try:
    import httpx
except ImportError:
    httpx = None

from backend.config import (
    EMBED_MODEL,
    EMBEDDING_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
    OLLAMA_MODEL,
)

logger = logging.getLogger(__name__)

# Configure Google GenAI if available and configured
try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    genai = None


# ─── LLM Generation ───────────────────────────────────────────

def generate_completion(prompt: str, model_override: Optional[str] = None) -> str:
    """
    Generate text using the configured LLM_PROVIDER ('ollama' or 'gemini').
    """
    provider = LLM_PROVIDER.lower().strip()

    if provider == "ollama":
        if not httpx:
            return "The 'httpx' package is required for Ollama provider. Please install it."
        model_name = model_override or OLLAMA_MODEL
        url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
        }
        try:
            with httpx.Client(timeout=90.0) as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    logger.error(f"Ollama generation failed ({res.status_code}): {res.text}")
                    return f"Ollama error ({res.status_code}): Please ensure model '{model_name}' is installed via 'ollama pull {model_name}'."
                data = res.json()
                return data.get("response", "").strip()
        except httpx.ConnectError:
            msg = f"Could not connect to Ollama at {OLLAMA_BASE_URL}. Is Ollama running? (Try running 'ollama serve')"
            logger.error(msg)
            return msg
        except Exception as e:
            logger.error(f"Ollama generation exception: {e}", exc_info=True)
            return f"Failed to generate response using Ollama: {e}"

    elif provider == "gemini":
        if not genai or not GEMINI_API_KEY:
            return "Gemini API key is not configured. Set GEMINI_API_KEY or switch LLM_PROVIDER to 'ollama'."
        try:
            model = genai.GenerativeModel(model_override or GEMINI_MODEL)
            response = model.generate_content(prompt)
            return response.text.strip() if response and response.text else "Empty response from Gemini."
        except Exception as e:
            logger.error(f"Gemini LLM error: {e}", exc_info=True)
            return f"Failed to generate response using Gemini: {e}"

    else:
        return f"Unsupported LLM_PROVIDER '{provider}'. Supported options: 'ollama', 'gemini'."


# ─── Embeddings ────────────────────────────────────────────────

def embed_query_text(query: str) -> List[float]:
    """
    Embed a single query using the configured EMBEDDING_PROVIDER ('ollama' or 'gemini').
    """
    if not query or not query.strip():
        return []

    provider = EMBEDDING_PROVIDER.lower().strip()

    if provider == "ollama":
        model_name = OLLAMA_EMBED_MODEL
        base_url = OLLAMA_BASE_URL.rstrip("/")
        # Try newer /api/embed first, fall back to /api/embeddings
        try:
            with httpx.Client(timeout=60.0) as client:
                embed_res = client.post(
                    f"{base_url}/api/embed",
                    json={"model": model_name, "input": query},
                )
                if embed_res.status_code == 200:
                    embeddings = embed_res.json().get("embeddings", [])
                    if embeddings and isinstance(embeddings[0], list):
                        return embeddings[0]
                
                # Fallback to older /api/embeddings
                fallback_res = client.post(
                    f"{base_url}/api/embeddings",
                    json={"model": model_name, "prompt": query},
                )
                if fallback_res.status_code == 200:
                    return fallback_res.json().get("embedding", [])
                
                logger.error(f"Ollama embedding failed ({fallback_res.status_code}): {fallback_res.text}")
                return []
        except Exception as e:
            logger.error(f"Error connecting to Ollama for embedding: {e}")
            return []

    elif provider == "gemini":
        if not genai or not GEMINI_API_KEY:
            logger.error("Gemini embedding requested but GEMINI_API_KEY is missing or genai not installed.")
            return []
        try:
            result = genai.embed_content(
                model=EMBED_MODEL,
                content=query,
                task_type="retrieval_query",
            )
            return result.get("embedding", [])
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}", exc_info=True)
            return []

    else:
        logger.error(f"Unsupported EMBEDDING_PROVIDER '{provider}'.")
        return []


def embed_document_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a batch of document texts using the configured EMBEDDING_PROVIDER ('ollama' or 'gemini').
    """
    if not texts:
        return []

    provider = EMBEDDING_PROVIDER.lower().strip()

    if provider == "ollama":
        model_name = OLLAMA_EMBED_MODEL
        base_url = OLLAMA_BASE_URL.rstrip("/")
        embeddings: List[List[float]] = []

        try:
            with httpx.Client(timeout=90.0) as client:
                # Try batch with /api/embed
                batch_res = client.post(
                    f"{base_url}/api/embed",
                    json={"model": model_name, "input": texts},
                )
                if batch_res.status_code == 200:
                    data = batch_res.json().get("embeddings", [])
                    if len(data) == len(texts):
                        return data

                # Fallback to sequential /api/embeddings
                for text in texts:
                    res = client.post(
                        f"{base_url}/api/embeddings",
                        json={"model": model_name, "prompt": text},
                    )
                    if res.status_code == 200:
                        embeddings.append(res.json().get("embedding", []))
                    else:
                        embeddings.append([])
            return embeddings
        except Exception as e:
            logger.error(f"Ollama batch embedding failed: {e}")
            return [[] for _ in texts]

    elif provider == "gemini":
        if not genai or not GEMINI_API_KEY:
            logger.error("Gemini embedding requested but GEMINI_API_KEY is missing or genai not installed.")
            return [[] for _ in texts]
        embeddings: List[List[float]] = []
        batch_size = 100
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                result = genai.embed_content(
                    model=EMBED_MODEL,
                    content=batch,
                    task_type="retrieval_document",
                )
                embeddings.extend(result.get("embedding", []))
            return embeddings
        except Exception as e:
            logger.error(f"Gemini batch embedding error: {e}", exc_info=True)
            return [[] for _ in texts]

    else:
        logger.error(f"Unsupported EMBEDDING_PROVIDER '{provider}'.")
        return [[] for _ in texts]
