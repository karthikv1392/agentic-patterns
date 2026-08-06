"""RAG (Retrieval-Augmented Generation) — single-agent pattern demo.

A local JSON knowledge base is used as the document store. When the user
submits a query, relevant chunks are retrieved via a lightweight TF-IDF-style
keyword scorer (no external vector-DB required). The retrieved context is then
injected into an augmented prompt that is sent to the LLM, grounding the final
answer in the knowledge base rather than relying solely on the model's
parametric memory.

Flow:
    User Query
        → [Retriever]  scores every KB chunk and picks top-k
        → [Augmenter]  builds prompt = query + retrieved context
        → [LLM]        generates grounded final answer
"""

import json
import math
import os
import re
from collections import Counter

from utils import generate_response

# ---------------------------------------------------------------------------
# Path to the knowledge base file (same directory as this module)
# ---------------------------------------------------------------------------
_KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.json")


# ---------------------------------------------------------------------------
# Knowledge base loading
# ---------------------------------------------------------------------------

def _load_knowledge_base() -> list[dict]:
    """Load and return all chunks from the JSON knowledge base."""
    with open(_KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Retrieval helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Lowercase and extract word tokens, stripping punctuation."""
    return re.findall(r"\b[a-z]+\b", text.lower())


def _score_chunk(query_tokens: list[str], chunk_text: str) -> float:
    """Score a chunk against query tokens using a TF-based overlap measure.

    For each unique query token that appears in the chunk, accumulates
    log(1 + 10 * tf) where tf = term_count / chunk_length. This rewards
    chunks that contain many of the query terms at high frequency while
    gently penalising very long chunks.
    """
    chunk_tokens = _tokenize(chunk_text)
    if not chunk_tokens:
        return 0.0

    tf_map = Counter(chunk_tokens)
    total = len(chunk_tokens)
    score = 0.0
    for token in set(query_tokens):
        tf = tf_map.get(token, 0) / total
        score += math.log(1.0 + 10.0 * tf)
    return score


def _retrieve(query: str, knowledge_base: list[dict], top_k: int = 3) -> list[dict]:
    """Return the top_k most relevant chunks for the query.

    Chunks with a score of 0 (no query term overlap) are excluded so the
    augmented prompt is never padded with irrelevant content.
    """
    query_tokens = _tokenize(query)
    scored = []
    for chunk in knowledge_base:
        combined_text = chunk["title"] + " " + chunk["content"]
        score = _score_chunk(query_tokens, combined_text)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_rag(user_query: str, top_k: int = 3) -> dict:
    """Run the RAG pipeline.

    Steps:
        1. Load the knowledge base from disk.
        2. Retrieve the top_k most relevant chunks for the user query.
        3. Build an augmented prompt combining the query and retrieved context.
        4. Call the LLM to generate a grounded final answer.

    Args:
        user_query: The user's question or task.
        top_k:      Number of knowledge-base chunks to retrieve (default 3).

    Returns a dict with keys:
        retrieved_chunks  — list of dicts, each with 'id', 'title', 'content'
        augmented_prompt  — the full prompt sent to the LLM
        final_output      — the LLM's grounded response
    """

    # Step 1 — Load knowledge base
    knowledge_base = _load_knowledge_base()

    # Step 2 — Retrieve relevant chunks
    retrieved_chunks = _retrieve(user_query, knowledge_base, top_k=top_k)

    # Step 3 — Build augmented prompt
    if retrieved_chunks:
        context_sections = "\n\n".join(
            f"[{i + 1}] {chunk['title']}\n{chunk['content']}"
            for i, chunk in enumerate(retrieved_chunks)
        )
        augmented_prompt = (
            "You are a knowledgeable assistant. Use the following retrieved "
            "context passages to answer the user's question accurately and "
            "completely. Base your answer primarily on the provided context. "
            "If the context does not fully cover the question, you may supplement "
            "with your general knowledge but clearly indicate when you are doing so.\n\n"
            "--- Retrieved Context ---\n"
            f"{context_sections}\n"
            "--- End of Context ---\n\n"
            f"User Question: {user_query}\n\n"
            "Provide a comprehensive, well-structured answer in markdown format."
        )
    else:
        # No relevant chunks found — fall back to pure LLM without context
        augmented_prompt = (
            "You are a knowledgeable assistant. Answer the following question "
            "as accurately as possible. Note: no relevant documents were found "
            "in the knowledge base for this query, so this answer is based "
            "entirely on your general knowledge.\n\n"
            f"User Question: {user_query}\n\n"
            "Provide a comprehensive, well-structured answer in markdown format."
        )

    # Step 4 — Generate grounded response
    final_output = generate_response(augmented_prompt)

    return {
        "retrieved_chunks": retrieved_chunks,
        "augmented_prompt": augmented_prompt,
        "final_output": final_output,
    }


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    default_query = "What is Retrieval-Augmented Generation and why does it reduce hallucinations?"
    print(f"Running RAG with query: {default_query!r}\n")

    result = run_rag(default_query)

    print("=" * 60)
    print(f"RETRIEVED CHUNKS ({len(result['retrieved_chunks'])} found)")
    print("=" * 60)
    for i, chunk in enumerate(result["retrieved_chunks"], 1):
        print(f"\n[{i}] {chunk['title']} (id: {chunk['id']})")
        print(chunk["content"][:200] + "...")

    print()
    print("=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(result["final_output"])
