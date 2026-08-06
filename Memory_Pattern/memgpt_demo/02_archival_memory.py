"""
02_archival_memory.py - Archival Memory (Long-Term / RAG)
==========================================================

CONCEPT: Archival Memory
-------------------------
Archival memory is OUT-OF-CONTEXT long-term storage.
Think of it as a personal knowledge base / external database.

It lives OUTSIDE the context window but the agent can:
  archival_memory_search("query")  → semantic search, pulls results IN
  archival_memory_insert("text")   → stores a new fact/note

This is exactly how RAG (Retrieval-Augmented Generation) works —
the agent decides when to search and what to retrieve.

Memory Hierarchy (MemGPT):
  ┌──────────────────────────────────────┐
  │         Context Window               │
  │  [persona] [human] [tasks]           │  ← Core Memory (always in)
  │  [Recent messages]                   │
  └──────────────────────────────────────┘
           ↓ agent tools ↓
  ┌──────────────────────────────────────┐
  │  Archival Storage (vector DB)        │  ← THIS FILE
  │  • Stores unlimited facts/notes      │
  │  • Searched semantically on demand   │
  │  • Persists across sessions          │
  └──────────────────────────────────────┘

This demo:
  1. Pre-load facts into archival memory (like populating a knowledge base)
  2. Ask the agent questions that require archival search
  3. Watch the agent call archival_memory_search automatically
  4. Manually read archival passages via the API
"""

from config import get_client, DEFAULT_MODEL, DEFAULT_EMBEDDING


# ── Knowledge base facts to load into archival memory ────────────────────────
KNOWLEDGE_BASE = [
    "Python was created by Guido van Rossum and first released in 1991.",
    "NumPy is a Python library for numerical computation using n-dimensional arrays.",
    "PyTorch uses dynamic computation graphs, making it popular for research.",
    "TensorFlow was developed by Google Brain and released in 2015.",
    "The fast.ai library is built on top of PyTorch and designed for practitioners.",
    "AWS Solutions Architect exam has two levels: Associate and Professional.",
    "The Associate exam covers EC2, S3, RDS, VPC, IAM, and Lambda as core topics.",
    "Spaced repetition is proven to improve long-term retention of information.",
    "The Feynman Technique: explain a concept simply as if teaching a 12-year-old.",
    "Active recall beats passive re-reading for learning retention by 3-4x.",
]


def main():
    client = get_client()

    # ── 1. Create agent ───────────────────────────────────────────────────────
    print("=== Creating agent with archival memory enabled ===")

    agent = client.agents.create(
        name="knowledge-assistant",
        model=DEFAULT_MODEL,
        embedding=DEFAULT_EMBEDDING,  # Required for semantic search in archival
        memory_blocks=[
            {
                "label": "persona",
                "value": (
                    "I am a knowledgeable study assistant. "
                    "When answering questions, I always search my archival memory "
                    "for relevant facts before responding. "
                    "I store important information I learn for future reference."
                ),
            },
            {
                "label": "human",
                "value": "A student studying ML and AWS certifications.",
            },
        ],
    )
    print(f"Agent created: {agent.id}")

    # ── 2. Try to pre-load knowledge base via API ─────────────────────────────
    print(f"\n=== Attempting to load {len(KNOWLEDGE_BASE)} facts into archival memory ===")
    print("  NOTE: Requires an embedding backend. Local Docker uses OpenAI embeddings.")
    print("        Falling back to teaching the agent facts via conversation instead.\n")

    archival_via_api = False
    for i, fact in enumerate(KNOWLEDGE_BASE):
        try:
            client.agents.passages.create(agent_id=agent.id, text=fact)
            print(f"  Stored [{i+1}]: {fact[:60]}...")
            archival_via_api = True
        except Exception:
            print(f"  [Embedding backend unavailable — skipping direct API insert]")
            break

    # ── 3. Teach facts via conversation (works without embeddings) ────────────
    # The agent stores facts in its core memory or can be asked to recall them.
    if not archival_via_api:
        print("\n=== Teaching facts via conversation (archival concept demo) ===")
        facts_summary = "\n".join(f"- {f}" for f in KNOWLEDGE_BASE)
        resp = client.agents.messages.create(
            agent_id=agent.id,
            messages=[{"role": "user", "content": (
                f"Please store these facts in your memory for later retrieval:\n{facts_summary}"
            )}],
        )
        for msg in resp.messages:
            if not hasattr(msg, "message_type"):
                continue
            if msg.message_type == "tool_call_message":
                print(f"  [Tool: {msg.tool_call.name}] {msg.tool_call.arguments[:80]}")
            elif msg.message_type == "assistant_message":
                print(f"\nAgent: {msg.content}")

    # ── 4. Ask questions — agent answers from what it knows ───────────────────
    questions = [
        "What do you know about PyTorch vs TensorFlow?",
        "What topics should I focus on for the AWS Associate exam?",
        "What study techniques are most effective for long-term retention?",
    ]

    for question in questions:
        print(f"\n=== Q: {question} ===")
        resp = client.agents.messages.create(
            agent_id=agent.id,
            messages=[{"role": "user", "content": question}],
        )
        for msg in resp.messages:
            if not hasattr(msg, "message_type"):
                continue
            if msg.message_type == "tool_call_message":
                name = msg.tool_call.name
                args = msg.tool_call.arguments
                if "archival" in name:
                    print(f"  [Archival search] query={args}")
                elif "conversation" in name:
                    print(f"  [Recall search] query={args}")
                else:
                    print(f"  [Tool: {name}]")
            elif msg.message_type == "tool_return_message":
                print(f"  [Result] {str(msg.tool_return)[:120]}...")
            elif msg.message_type == "assistant_message":
                print(f"\nAgent: {msg.content}")

    # ── 5. Ask agent to remember a new insight ────────────────────────────────
    print("\n=== Agent stores new insight ===")
    resp = client.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": (
            "I just learned that the Pomodoro technique (25-min focus blocks) "
            "really helps me stay on track. Please remember this for me."
        )}],
    )
    for msg in resp.messages:
        if not hasattr(msg, "message_type"):
            continue
        if msg.message_type == "tool_call_message":
            print(f"  [Tool: {msg.tool_call.name}] {msg.tool_call.arguments[:80]}")
        elif msg.message_type == "assistant_message":
            print(f"\nAgent: {msg.content}")

    passages = list(client.agents.passages.list(agent_id=agent.id))
    print(f"\nArchival passages via API: {len(passages)}")

    print(f"\n[Done] Agent ID: {agent.id}")
    return agent.id


if __name__ == "__main__":
    main()
