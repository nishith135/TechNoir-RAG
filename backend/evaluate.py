from __future__ import annotations

import requests
from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset
from ragas.metrics import AnswerRelevancy, ContextPrecision, Faithfulness
from ragas.llms import LangchainLLMWrapper
from langchain_ollama import ChatOllama

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from backend.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.retrieval import hybrid_retrieve, rerank


def _generate_answer(question: str, chunks: list[dict]) -> str:
    """Call the local Ollama LLM exactly like the /query endpoint."""
    user_prompt = build_user_prompt(question=question, chunks=chunks)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"LLM error: {str(e)}"


def evaluate_rag(
    test_questions: list[str],
    collection_name: str,
) -> dict:
    """
    Run ragas evaluation over *test_questions* against *collection_name*.
    """
    samples: list[dict] = []

    for question in test_questions:
        raw_chunks = hybrid_retrieve(
            query=question, collection_name=collection_name, k=10
        )
        chunks = rerank(query=question, chunks=raw_chunks, top_n=5)
        answer = _generate_answer(question, chunks)
        contexts = [c.get("text", "") for c in chunks]

        samples.append(
            {
                "user_input": question,
                "response": answer,
                "retrieved_contexts": contexts,
                "reference": "",
            }
        )

    eval_dataset = EvaluationDataset.from_list(samples)

    evaluator_llm = LangchainLLMWrapper(
        ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
    )

    result = evaluate(
        dataset=eval_dataset,
        metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision()],
        llm=evaluator_llm,
    )

    return {
        "faithfulness": result["faithfulness"],
        "answer_relevancy": result["answer_relevancy"],
        "context_precision": result["context_precision"],
    }
