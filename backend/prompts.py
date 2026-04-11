from __future__ import annotations

from typing import List

from backend.config import GEMINI_MODEL

SYSTEM_PROMPT: str = (
    f"You are a RAG assistant using the model `{GEMINI_MODEL}`.\n\n"
    "Answer ONLY using the provided context. "
    "If the answer is not in the context, respond with "
    "\"I don't have enough information in the provided document to answer that.\""
)


def build_user_prompt(question: str, chunks: list[dict]) -> str:
    """
    Format retrieved chunks as numbered context blocks, then append the question.
    """
    context_blocks: List[str] = []

    for idx, chunk in enumerate(chunks, start=1):
        page = chunk.get("page", "")
        source = chunk.get("source", "")
        text = chunk.get("text", "")

        context_blocks.append(
            f"Context Block {idx}:\n"
            f"Source: {source}\n"
            f"Page: {page}\n"
            f"Text: {text}\n"
        )

    context_str = "\n".join(context_blocks).strip()
    return (
        "Use the following context to answer the question.\n\n"
        f"{context_str}\n\n"
        f"Question: {question}"
    )

