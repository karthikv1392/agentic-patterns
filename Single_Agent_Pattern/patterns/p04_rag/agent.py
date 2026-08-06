"""RAG (Retrieval-Augmented Generation) — agent.

The user asks a question. The agent:
  1. Retrieves relevant chunks from the knowledge base  via retriever.py
  2. Builds an augmented prompt (query + retrieved context)
  3. Calls the LLM to produce a grounded final answer

The LLM's answer is *grounded* in retrieved documents rather than
relying solely on parametric (training-time) memory.
"""

from shared.llm import generate_response
from patterns.p04_rag.retriever import retrieve


def run(user_query: str, top_k: int = 3) -> dict:
    """
    Args:
        user_query : The user's question.
        top_k      : Number of KB chunks to retrieve (default 3).

    Returns:
        retrieved_chunks : list of {id, title, content} dicts
        augmented_prompt : The full prompt sent to the LLM
        final_output     : Grounded LLM response
    """

    # Step 1: retrieve
    chunks = retrieve(user_query, top_k=top_k)

    # Step 2: build augmented prompt
    if chunks:
        context_block = "\n\n".join(
            f"[{i+1}] {c['title']}\n{c['content']}" for i, c in enumerate(chunks)
        )
        augmented_prompt = (
            "You are a knowledgeable assistant. Use the retrieved context below "
            "to answer the user's question accurately. Base your answer primarily "
            "on the provided context; supplement with general knowledge only if "
            "needed (and say so clearly).\n\n"
            "--- Retrieved Context ---\n"
            f"{context_block}\n"
            "--- End of Context ---\n\n"
            f"User Question: {user_query}\n\n"
            "Provide a comprehensive, well-structured answer in markdown."
        )
    else:
        augmented_prompt = (
            "You are a knowledgeable assistant. No relevant documents were found "
            "in the knowledge base; answer from general knowledge.\n\n"
            f"User Question: {user_query}\n\n"
            "Provide a comprehensive, well-structured answer in markdown."
        )

    # Step 3: generate
    final_output = generate_response(augmented_prompt)

    return {
        "retrieved_chunks": chunks,
        "augmented_prompt": augmented_prompt,
        "final_output": final_output,
    }
