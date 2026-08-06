"""RAG retriever — isolated retrieval logic.

Implements a lightweight TF-based keyword retriever over the local
JSON knowledge base. No external vector DB or embeddings required.

Separated from agent.py so learners can see that retrieval is its
own distinct component in the RAG pipeline.
"""

import json
import math
import os
import re
from collections import Counter

_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "shared", "knowledge_base.json")


def load_knowledge_base() -> list[dict]:
    """Load all chunks from the JSON knowledge base."""
    with open(_KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b[a-z]+\b", text.lower())


def _score(query_tokens: list[str], chunk_text: str) -> float:
    """TF-based overlap score: sum of log(1 + 10*tf) for each query term."""
    tokens = _tokenize(chunk_text)
    if not tokens:
        return 0.0
    tf = Counter(tokens)
    total = len(tokens)
    return sum(math.log(1.0 + 10.0 * tf.get(t, 0) / total) for t in set(query_tokens))


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Return the top_k most relevant knowledge-base chunks for *query*.

    Chunks with zero overlap are excluded so the LLM never receives
    irrelevant context padding.
    """
    kb = load_knowledge_base()
    query_tokens = _tokenize(query)
    scored = sorted(
        [(chunk, _score(query_tokens, chunk["title"] + " " + chunk["content"])) for chunk in kb],
        key=lambda x: x[1], reverse=True,
    )
    return [chunk for chunk, score in scored[:top_k] if score > 0]
