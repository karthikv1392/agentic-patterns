"""
05_shared_memory_agents.py - Shared Memory Blocks Across Agents
================================================================

CONCEPT: Shared Memory Blocks
------------------------------
In Letta, a memory block can be SHARED between multiple agents.

When Agent A updates a shared block, Agent B sees the change immediately
(because both read from the same DB record).

This enables powerful multi-agent patterns:
  • Supervisor → Worker: supervisor writes task specs, worker reads them
  • Specialist agents contribute to a shared knowledge pool
  • Background agent updates primary agent's memory while it's idle

Architecture:
  ┌─────────────┐     shared block     ┌─────────────┐
  │  Agent A    │ ←─────────────────→  │  Agent B    │
  │ (Planner)   │    [project_status]  │ (Executor)  │
  └─────────────┘                      └─────────────┘
         │                                    │
         └──────────── same block_id ─────────┘

This demo use case: Learning Team
  • Planner agent  — breaks down the study goal, writes to shared block
  • Tracker agent  — reads the shared block and monitors/updates progress
  • Both agents share a "project_status" block
"""

from config import get_client, DEFAULT_MODEL, DEFAULT_EMBEDDING


def chat_and_print(client, agent_id: str, agent_name: str, user_msg: str):
    print(f"\n[{agent_name}] User: {user_msg}")
    resp = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": user_msg}],
    )
    for msg in resp.messages:
        if not hasattr(msg, "message_type"):
            continue
        if msg.message_type == "assistant_message":
            print(f"[{agent_name}] Agent: {msg.content}")
        elif msg.message_type == "tool_call_message":
            name = msg.tool_call.name
            print(f"[{agent_name}]   [Tool: {name}] {msg.tool_call.arguments[:60]}")


def show_shared_block(client, block_id: str, block_label: str):
    """Read the shared block directly from the block store."""
    block = client.blocks.retrieve(block_id=block_id)
    print(f"\n  [Shared block: {block_label}]\n  {block.value}\n")


def main():
    client = get_client()

    # ── 1. Create the shared memory block ────────────────────────────────────
    print("=== Creating shared 'project_status' block ===")

    shared_block = client.blocks.create(
        label="project_status",
        value=(
            "PROJECT: Alex's 8-Week Study Plan\n"
            "STATUS: Not started\n"
            "PLANNER: (waiting for assignment)\n"
            "TRACKER: (no updates yet)\n"
        ),
        limit=5000,  # character limit for this block
    )
    print(f"Shared block created: {shared_block.id}")

    # ── 2. Create Planner agent — attaches shared block ───────────────────────
    print("\n=== Creating Planner agent ===")

    planner = client.agents.create(
        name="planner-agent",
        model=DEFAULT_MODEL,
        embedding=DEFAULT_EMBEDDING,
        memory_blocks=[
            {
                "label": "persona",
                "value": (
                    "I am the Planner agent. My job is to create detailed study plans. "
                    "I write my plans to the 'project_status' shared block so other agents "
                    "can see and act on the plan."
                ),
            },
            {
                "label": "human",
                "value": "Alex, ML student. 8-week plan: fast.ai + AWS exam.",
            },
        ],
        # Attach the existing shared block
        block_ids=[shared_block.id],
    )
    print(f"Planner agent: {planner.id}")

    # ── 3. Create Tracker agent — also attaches the SAME shared block ─────────
    print("\n=== Creating Tracker agent (shares same block) ===")

    tracker = client.agents.create(
        name="tracker-agent",
        model=DEFAULT_MODEL,
        embedding=DEFAULT_EMBEDDING,
        memory_blocks=[
            {
                "label": "persona",
                "value": (
                    "I am the Tracker agent. My job is to monitor study progress. "
                    "I read the 'project_status' shared block to see the plan, "
                    "then update it with progress reports and encouragement."
                ),
            },
            {
                "label": "human",
                "value": "Alex, ML student. Currently in week 1 of the plan.",
            },
        ],
        # Attach the SAME shared block
        block_ids=[shared_block.id],
    )
    print(f"Tracker agent: {tracker.id}")

    # ── 4. Planner writes to shared block ────────────────────────────────────
    print("\n=== Planner creates the study plan (writes to shared block) ===")
    show_shared_block(client, shared_block.id, "project_status")

    chat_and_print(
        client,
        planner.id,
        "Planner",
        (
            "Please create a high-level 8-week study plan for Alex in the project_status block. "
            "Week 1-4: fast.ai lessons + AWS fundamentals. Week 5-8: AWS practice exams. "
            "Write a clear weekly breakdown into the shared project_status block."
        ),
    )

    print("\n=== Shared block AFTER planner writes ===")
    show_shared_block(client, shared_block.id, "project_status")

    # ── 5. Tracker reads the same block — sees planner's updates ─────────────
    print("=== Tracker reads shared block and reports on week 1 ===")

    chat_and_print(
        client,
        tracker.id,
        "Tracker",
        (
            "Alex just completed week 1. He finished fast.ai lessons 1-3 and "
            "started the AWS Cloud Practitioner module. Please update the project_status "
            "block with this progress and give Alex an encouraging message."
        ),
    )

    print("\n=== Shared block AFTER tracker updates ===")
    show_shared_block(client, shared_block.id, "project_status")

    # ── 6. Planner sees tracker's update without any API call ────────────────
    print("=== Planner checks shared block (automatically sees tracker's update) ===")

    chat_and_print(
        client,
        planner.id,
        "Planner",
        "What's the current status of Alex's study plan based on what you know?",
    )

    # ── 7. Inspect shared block one last time ────────────────────────────────
    print("\n=== Final shared block state ===")
    show_shared_block(client, shared_block.id, "project_status")

    print("\n=== Summary ===")
    print(f"  Shared block ID:  {shared_block.id}")
    print(f"  Planner agent ID: {planner.id}")
    print(f"  Tracker agent ID: {tracker.id}")
    print("\n  Both agents share the same memory block — any update is immediately")
    print("  visible to all agents without any manual synchronization.")

    return planner.id, tracker.id, shared_block.id


if __name__ == "__main__":
    main()
