"""
03_recall_memory.py - Recall Memory (Conversation History)
===========================================================

CONCEPT: Recall Memory
-----------------------
Recall memory is the agent's full conversation history — automatically
saved to disk/database by Letta across ALL sessions.

It lives OUTSIDE the context window (unlike recent messages in the buffer)
but the agent can search it with:
  conversation_search("query")  → semantic search over all past messages
  conversation_search_date(...)  → search by time range

This solves a key limitation of plain LLMs:
  Without recall: "I don't remember what we talked about last week."
  With recall:    Agent searches history → finds the relevant exchange.

Memory Hierarchy (MemGPT):
  ┌──────────────────────────────────────┐
  │         Context Window               │
  │  [persona] [human] [tasks]           │  ← Core Memory
  │  [Last N messages (message buffer)]  │  ← Recent in-context
  └──────────────────────────────────────┘
           ↓ agent tools ↓
  ┌──────────────────────────────────────┐
  │  Recall Storage (conversation DB)   │  ← THIS FILE
  │  • Every message ever sent           │
  │  • Searched semantically on demand   │
  │  • Enables cross-session memory      │
  └──────────────────────────────────────┘

This demo:
  1. Have a multi-turn conversation with the agent
  2. Retrieve the full message history via API
  3. Ask the agent to recall something from "earlier" in the conversation
  4. Demonstrate cross-session memory (reuse an existing agent)
"""

from config import get_client, DEFAULT_MODEL, DEFAULT_EMBEDDING


def print_message(msg):
    if not hasattr(msg, "message_type"):
        return
    mtype = msg.message_type
    if mtype == "assistant_message":
        print(f"Agent: {msg.content}")
    elif mtype == "tool_call_message":
        name = msg.tool_call.name
        if "conversation" in name or "recall" in name:
            print(f"  [Recall search] {msg.tool_call.arguments}")
        elif "archival" in name:
            print(f"  [Archival search] {msg.tool_call.arguments}")
    elif mtype == "tool_return_message":
        snippet = str(msg.tool_return)[:100]
        print(f"  [Search result] {snippet}...")


def chat(client, agent_id: str, user_msg: str) -> None:
    """Send a message and print the response."""
    print(f"\nUser: {user_msg}")
    resp = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": user_msg}],
    )
    for msg in resp.messages:
        print_message(msg)


def main():
    client = get_client()

    # ── 1. Create agent ───────────────────────────────────────────────────────
    print("=== Creating agent ===")
    agent = client.agents.create(
        name="recall-demo-agent",
        model=DEFAULT_MODEL,
        embedding=DEFAULT_EMBEDDING,
        memory_blocks=[
            {
                "label": "persona",
                "value": (
                    "I am a helpful assistant with perfect memory. "
                    "When a user references past conversations, I search my recall "
                    "memory to find the relevant exchange and continue seamlessly."
                ),
            },
            {
                "label": "human",
                "value": "No information yet.",
            },
        ],
    )
    print(f"Agent created: {agent.id}")

    # ── 2. Build up a conversation history ───────────────────────────────────
    print("\n=== Building conversation history ===")

    chat(client, agent.id, "My name is Jordan. I'm learning Python for data science.")
    chat(client, agent.id, "My favourite Python library so far is Pandas — it makes data wrangling so easy.")
    chat(client, agent.id, "I struggled a lot with understanding list comprehensions at first, but I've got them now.")
    chat(client, agent.id, "I also want to learn SQL. Any tips on where to start?")
    chat(client, agent.id, "Great, I'll check out SQLZoo. By the way, I prefer video tutorials over reading docs.")

    # ── 3. View full recall memory via API ────────────────────────────────────
    print("\n=== Full recall memory (conversation history) via API ===")
    all_messages = list(client.agents.messages.list(agent_id=agent.id))
    print(f"  Total messages in recall store: {len(all_messages)}")

    # Show a few
    print("\n  Recent messages snapshot:")
    for msg in all_messages[-6:]:
        mtype = getattr(msg, "message_type", "unknown")
        if mtype == "user_message":
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            print(f"  User:  {content[:80]}")
        elif mtype == "assistant_message":
            print(f"  Agent: {msg.content[:80]}")

    # ── 4. Ask agent to recall something from earlier ────────────────────────
    print("\n=== Testing recall: agent should search history ===")

    chat(
        client,
        agent.id,
        "Hey, what was that Python library I mentioned I really liked earlier?",
    )

    chat(
        client,
        agent.id,
        "And what did I say about list comprehensions?",
    )

    # ── 5. Cross-session recall — same agent, fresh "session" ────────────────
    # In a real app you'd just save the agent_id and re-connect later.
    # Here we simulate by sending a message that implies time has passed.
    print("\n=== Cross-session recall (simulated) ===")

    chat(
        client,
        agent.id,
        "I'm back! Last time we talked, what learning goals did we discuss? "
        "Specifically, what did I want to learn other than Python?",
    )

    print(f"\n[Done] Agent ID: {agent.id}")
    print("       Save this ID to test TRUE cross-session recall:")
    print(f"       python 03_recall_memory.py --resume {agent.id}")
    return agent.id


if __name__ == "__main__":
    import sys
    main()
