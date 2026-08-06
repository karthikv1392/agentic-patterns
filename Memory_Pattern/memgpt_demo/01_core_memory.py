"""
01_core_memory.py - Core (In-Context) Memory Blocks
====================================================

CONCEPT: Core Memory
--------------------
Core memory is what lives INSIDE the agent's context window at all times.
It is organized into named "blocks" — each block is a labelled string the
agent can read AND update via built-in memory tools:

  core_memory_append  → append text to a block
  core_memory_replace → replace the value of a block

Common built-in blocks:
  "human"   — what the agent knows about the user
  "persona" — the agent's personality / role description

You can also add CUSTOM blocks (e.g. "tasks", "scratchpad").

Memory Hierarchy (MemGPT architecture):
  ┌─────────────────────────────────────────────┐
  │         Context Window (finite)              │
  │  ┌───────────┐  ┌──────────┐  ┌──────────┐ │  ← CORE MEMORY
  │  │  persona  │  │  human   │  │  tasks   │ │    (always visible)
  │  └───────────┘  └──────────┘  └──────────┘ │
  │  ┌──────────────────────────────────────┐   │
  │  │         Recent Messages              │   │
  │  └──────────────────────────────────────┘   │
  └─────────────────────────────────────────────┘
         │                      │
  Archival Storage         Recall Storage
  (long-term facts)        (full chat history)
  [OUT of context]         [OUT of context]

This demo:
  1. Create an agent with human + persona + custom "tasks" blocks
  2. Chat with it — watch it self-update the "human" block
  3. Read memory blocks directly via the API
  4. Manually update a memory block from outside the agent
"""

from config import get_client, DEFAULT_MODEL, DEFAULT_EMBEDDING


def print_block(client, agent_id: str, label: str):
    """Helper to print the current value of a memory block."""
    block = client.agents.blocks.retrieve(agent_id=agent_id, block_label=label)
    print(f"\n  [{label} block]\n  {block.value}\n")


def main():
    client = get_client()

    # ── 1. Create agent with core memory blocks ──────────────────────────────
    print("=== Creating agent with core memory blocks ===")

    agent = client.agents.create(
        name="learning-assistant",
        model=DEFAULT_MODEL,
        embedding=DEFAULT_EMBEDDING,
        memory_blocks=[
            {
                "label": "persona",
                "value": (
                    "I am a friendly personal learning assistant named Sage. "
                    "I help users track their learning goals and study progress. "
                    "I always update my memory when I learn new things about the user."
                ),
            },
            {
                "label": "human",
                "value": "No information about this user yet.",
                # The agent will fill this in as the user shares details
            },
            {
                "label": "tasks",
                "value": "No active tasks yet.",
                # Custom block — agent can update this to track learning goals
            },
        ],
    )
    print(f"Agent created: {agent.id}")

    # ── 2. Show initial memory state ─────────────────────────────────────────
    print("\n=== Initial memory blocks ===")
    for label in ["persona", "human", "tasks"]:
        print_block(client, agent.id, label)

    # ── 3. Chat — agent learns about the user and updates memory ─────────────
    print("=== Sending first message (agent learns user name) ===")
    resp = client.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": (
            "Hi! My name is Alex. I'm studying machine learning "
            "and I want to finish the 'fast.ai' course this month."
        )}],
    )

    # Print assistant reply
    for msg in resp.messages:
        if hasattr(msg, "message_type"):
            if msg.message_type == "assistant_message":
                print(f"\nAgent: {msg.content}")
            elif msg.message_type == "tool_call_message":
                print(f"  [Tool call] {msg.tool_call.name}({msg.tool_call.arguments})")

    # ── 4. Show updated memory — agent should have updated "human" block ─────
    print("\n=== Memory blocks AFTER first message ===")
    for label in ["human", "tasks"]:
        print_block(client, agent.id, label)

    # ── 5. Second message — more info for the agent to remember ──────────────
    print("=== Sending second message (more context) ===")
    resp2 = client.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": (
            "I'm also preparing for the AWS Solutions Architect exam next month. "
            "I prefer studying in the evenings and hate textbook-style content."
        )}],
    )

    for msg in resp2.messages:
        if hasattr(msg, "message_type"):
            if msg.message_type == "assistant_message":
                print(f"\nAgent: {msg.content}")
            elif msg.message_type == "tool_call_message":
                print(f"  [Tool call] {msg.tool_call.name}({msg.tool_call.arguments})")

    print("\n=== Memory blocks AFTER second message ===")
    for label in ["human", "tasks"]:
        print_block(client, agent.id, label)

    # ── 6. EXTERNAL memory write — update from outside the agent ─────────────
    print("=== Manually updating 'tasks' block from outside the agent ===")
    client.agents.blocks.update(
        agent_id=agent.id,
        block_label="tasks",
        value=(
            "ACTIVE TASKS:\n"
            "1. fast.ai course — target: end of month\n"
            "2. AWS Solutions Architect exam — target: next month\n"
            "COMPLETED: None yet"
        ),
    )

    print("Updated! Verifying...")
    print_block(client, agent.id, "tasks")

    # ── 7. Agent picks up the externally-written memory ──────────────────────
    print("=== Agent uses the updated tasks block ===")
    resp3 = client.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": "What tasks am I currently working on?"}],
    )

    for msg in resp3.messages:
        if hasattr(msg, "message_type") and msg.message_type == "assistant_message":
            print(f"\nAgent: {msg.content}")

    print(f"\n[Done] Agent ID for future use: {agent.id}")
    return agent.id


if __name__ == "__main__":
    main()
