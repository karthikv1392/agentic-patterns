"""
04_scratchpad.py - Scratchpad Memory Block
===========================================

CONCEPT: Scratchpad (Custom In-Context Block)
----------------------------------------------
A scratchpad is a CUSTOM core memory block used as a temporary workspace.

The agent can use it to:
  • Jot down intermediate reasoning steps
  • Track the current sub-task it's solving
  • Store calculations or partial results
  • Leave notes for itself mid-task

Unlike archival memory (external DB), the scratchpad is ALWAYS in-context —
the agent sees it every turn without needing to search.

Unlike the "human" or "tasks" blocks, the scratchpad is intentionally
ephemeral — it gets overwritten each task.

Use Case: Multi-Step Problem Solving
--------------------------------------
When an agent works on a multi-step task, it can:
  Step 1 → write plan to scratchpad
  Step 2 → update scratchpad with progress
  Step 3 → clear scratchpad when done, write final result to tasks/archival

This demo:
  1. Create an agent with a scratchpad block
  2. Give it a multi-step study planning task
  3. Watch it use the scratchpad for working notes
  4. Read scratchpad state before/after
"""

from config import get_client, DEFAULT_MODEL, DEFAULT_EMBEDDING


def show_blocks(client, agent_id: str, labels: list[str]):
    print()
    for label in labels:
        block = client.agents.blocks.retrieve(agent_id=agent_id, block_label=label)
        print(f"  [{label}]\n  {block.value}\n")


def chat(client, agent_id: str, user_msg: str):
    print(f"\nUser: {user_msg}")
    resp = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": user_msg}],
    )
    for msg in resp.messages:
        if not hasattr(msg, "message_type"):
            continue
        if msg.message_type == "tool_call_message":
            name = msg.tool_call.name
            args = msg.tool_call.arguments
            if "core_memory" in name or "memory" in name.lower():
                print(f"  [Memory tool: {name}] {args[:80]}")
        elif msg.message_type == "assistant_message":
            print(f"Agent: {msg.content}")


def main():
    client = get_client()

    # ── 1. Create agent with scratchpad block ─────────────────────────────────
    print("=== Creating agent with scratchpad block ===")

    agent = client.agents.create(
        name="scratchpad-agent",
        model=DEFAULT_MODEL,
        embedding=DEFAULT_EMBEDDING,
        memory_blocks=[
            {
                "label": "persona",
                "value": (
                    "I am a study planning assistant. "
                    "When solving complex planning tasks, I use my scratchpad block "
                    "to write intermediate steps and working notes. "
                    "I always show my reasoning by updating my scratchpad as I work. "
                    "When I finish a task, I move the final plan to the 'tasks' block "
                    "and clear my scratchpad."
                ),
            },
            {
                "label": "human",
                "value": (
                    "Alex, ML student. Goals: finish fast.ai course + AWS exam. "
                    "Prefers evenings for study. Likes video content."
                ),
            },
            {
                "label": "scratchpad",
                "value": "[empty — agent uses this as a working notepad]",
                # This is the scratchpad — agent will overwrite it as it works
            },
            {
                "label": "tasks",
                "value": "No finalized plan yet.",
            },
        ],
    )
    print(f"Agent created: {agent.id}")

    # ── 2. Show initial state ─────────────────────────────────────────────────
    print("\n=== Initial memory blocks ===")
    show_blocks(client, agent.id, ["scratchpad", "tasks"])

    # ── 3. Complex task — requires scratchpad for multi-step reasoning ─────────
    print("=== Asking agent to build a study plan (multi-step) ===")
    chat(
        client,
        agent.id,
        (
            "I have 8 weeks until my AWS exam and I want to complete fast.ai at the same time. "
            "I can study 1.5 hours on weekdays and 3 hours on weekends. "
            "Please build me a detailed week-by-week study schedule. "
            "Use your scratchpad to work it out step by step."
        ),
    )

    # ── 4. Inspect scratchpad DURING the task ─────────────────────────────────
    print("\n=== Memory blocks DURING task ===")
    show_blocks(client, agent.id, ["scratchpad", "tasks"])

    # ── 5. Follow-up — agent adjusts the plan ────────────────────────────────
    chat(
        client,
        agent.id,
        "Actually, I have a holiday trip in week 4 — I can't study at all that week. "
        "Please adjust the plan.",
    )

    print("\n=== Memory blocks AFTER adjustment ===")
    show_blocks(client, agent.id, ["scratchpad", "tasks"])

    # ── 6. Ask agent to clear scratchpad ─────────────────────────────────────
    chat(
        client,
        agent.id,
        "Good. The plan looks solid. Please clear your scratchpad now since we're done planning.",
    )

    print("\n=== Final memory blocks ===")
    show_blocks(client, agent.id, ["scratchpad", "tasks"])

    print(f"\n[Done] Agent ID: {agent.id}")
    return agent.id


if __name__ == "__main__":
    main()
