"""
06_full_demo.py - Complete Memory System Demo
==============================================

The Full Picture: All Memory Types in One Agent
------------------------------------------------

This demo wires together ALL memory types in a single "Personal Study Assistant":

  Memory Type       | Location        | Persists  | Searched by
  ──────────────────────────────────────────────────────────────
  Core / User       | In-context      | Yes       | Always visible
  Core / Persona    | In-context      | Yes       | Always visible
  Core / Tasks      | In-context      | Yes       | Always visible
  Core / Scratchpad | In-context      | Yes       | Always visible
  Archival (RAG)    | Out-of-context  | Yes       | archival_memory_search
  Recall            | Out-of-context  | Yes       | conversation_search

MemGPT Memory Flow:
                    ┌─────────────────────────────────────────────┐
                    │           CONTEXT WINDOW                     │
  [System Prompt]   │  ┌──────────┐ ┌───────┐ ┌──────┐ ┌──────┐ │
  + [Memory Blocks] │  │ persona  │ │ human │ │tasks │ │scratch│ │
                    │  └──────────┘ └───────┘ └──────┘ └──────┘ │
                    │  ┌──────────────────────────────────────┐   │
                    │  │    Recent Messages (message buffer)  │   │
                    │  └──────────────────────────────────────┘   │
                    └──────────────┬──────────────────────────────┘
                                   │ agent tool calls
              ┌────────────────────┼────────────────────┐
              ▼                                         ▼
  ┌─────────────────────────┐             ┌─────────────────────────┐
  │   Archival Storage      │             │    Recall Storage        │
  │   (vector DB / RAG)     │             │    (conversation DB)     │
  │   archival_memory_search│             │    conversation_search   │
  │   archival_memory_insert│             │    (auto-populated)      │
  └─────────────────────────┘             └─────────────────────────┘

Run this to see the complete memory system in action.
"""

import time
from config import get_client, DEFAULT_MODEL, DEFAULT_EMBEDDING


def separator(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def chat(client, agent_id: str, user_msg: str, show_tools: bool = True):
    print(f"\nUser: {user_msg}")
    resp = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": user_msg}],
    )
    for msg in resp.messages:
        if not hasattr(msg, "message_type"):
            continue
        if msg.message_type == "tool_call_message" and show_tools:
            name = msg.tool_call.name
            args = msg.tool_call.arguments[:70]
            print(f"  [Tool: {name}] {args}")
        elif msg.message_type == "assistant_message":
            print(f"Agent: {msg.content}")


def show_all_memory(client, agent_id: str):
    """Print the state of all core memory blocks."""
    for label in ["human", "tasks", "scratchpad"]:
        try:
            block = client.agents.blocks.retrieve(agent_id=agent_id, block_label=label)
            print(f"\n  [{label}]\n  {block.value}")
        except Exception:
            pass  # Block might not exist

    try:
        passages = client.agents.passages.list(agent_id=agent_id)
        print(f"\n  [archival]  ({len(passages)} passages stored)")
        for p in passages[-3:]:
            print(f"    · {p.text[:70]}")
    except Exception:
        pass

    try:
        messages = client.agents.messages.list(agent_id=agent_id)
        user_msgs = [m for m in messages if getattr(m, "message_type", "") == "user_message"]
        print(f"\n  [recall]  ({len(user_msgs)} user messages in history)")
    except Exception:
        pass


def main():
    client = get_client()

    # ══════════════════════════════════════════════════════════════
    separator("STEP 1: Create agent with all memory blocks")
    # ══════════════════════════════════════════════════════════════

    agent = client.agents.create(
        name="full-memory-assistant",
        model=DEFAULT_MODEL,
        embedding=DEFAULT_EMBEDDING,
        memory_blocks=[
            # ── Persona: who the agent IS ──────────────────────────────────
            {
                "label": "persona",
                "value": (
                    "I am Sage, a personal study assistant with perfect memory. "
                    "I use all my memory systems effectively:\n"
                    "• I update the 'human' block when I learn about the user\n"
                    "• I update the 'tasks' block to track goals and progress\n"
                    "• I use the 'scratchpad' block for working notes on complex tasks\n"
                    "• I store important knowledge in archival memory for future retrieval\n"
                    "• I search conversation history when the user references past discussions"
                ),
            },
            # ── User memory: what we know about the user ───────────────────
            {
                "label": "human",
                "value": "No information about this user yet.",
            },
            # ── Task memory: current goals / todos ─────────────────────────
            {
                "label": "tasks",
                "value": "No active tasks yet.",
            },
            # ── Scratchpad: working memory for multi-step tasks ────────────
            {
                "label": "scratchpad",
                "value": "[empty]",
            },
        ],
    )
    print(f"Agent created: {agent.id}")
    print("\nInitial memory state:")
    show_all_memory(client, agent.id)

    # ══════════════════════════════════════════════════════════════
    separator("STEP 2: User introduces themselves (→ USER MEMORY)")
    # ══════════════════════════════════════════════════════════════

    chat(client, agent.id,
         "Hi Sage! I'm Sam, a software engineer at a startup. "
         "I'm learning ML on the side — specifically LLMs and fine-tuning. "
         "I have about 1 hour per day to study, usually in the morning.")

    print("\nMemory after introduction:")
    show_all_memory(client, agent.id)

    # ══════════════════════════════════════════════════════════════
    separator("STEP 3: Set goals (→ TASK MEMORY)")
    # ══════════════════════════════════════════════════════════════

    chat(client, agent.id,
         "My goals for this month: "
         "1. Understand transformer architecture from scratch. "
         "2. Fine-tune a small model on a custom dataset. "
         "3. Deploy it as a REST API. Can you track these for me?")

    print("\nMemory after goal-setting:")
    show_all_memory(client, agent.id)

    # ══════════════════════════════════════════════════════════════
    separator("STEP 4: Store knowledge in archival (→ ARCHIVAL / RAG)")
    # ══════════════════════════════════════════════════════════════

    # Pre-load domain knowledge the agent should "know"
    knowledge = [
        "Transformer architecture: self-attention + feed-forward layers, introduced in 'Attention is All You Need' (2017).",
        "LoRA (Low-Rank Adaptation) is a popular fine-tuning method that freezes base model weights and trains small adapter matrices.",
        "HuggingFace Transformers library: use `AutoModelForCausalLM.from_pretrained()` to load a model, `Trainer` class for fine-tuning.",
        "FastAPI is a high-performance Python web framework ideal for deploying ML models as REST APIs.",
        "Quantization (e.g., 4-bit via bitsandbytes) reduces VRAM requirements for running large models on consumer hardware.",
    ]

    print("Pre-loading knowledge base into archival memory...")
    archival_ok = True
    for fact in knowledge:
        try:
            client.agents.passages.create(agent_id=agent.id, text=fact)
            print(f"  + {fact[:70]}...")
        except Exception as e:
            print(f"  [Archival skipped — embedding backend unavailable in this local build]")
            print(f"  NOTE: The local Docker image requires OpenAI embeddings or Letta Cloud")
            print(f"        for archival/RAG. Core memory + recall still work fully.")
            archival_ok = False
            break

    if archival_ok:
        # Now ask a question requiring archival retrieval
        chat(client, agent.id,
             "What's the most practical way to fine-tune a model if I only have a laptop with 8GB VRAM?",
             show_tools=True)
        print("\nMemory after archival query:")
        show_all_memory(client, agent.id)
    else:
        print("\n  [Skipping archival query — passages could not be stored]")

    # ══════════════════════════════════════════════════════════════
    separator("STEP 5: Multi-step planning (→ SCRATCHPAD)")
    # ══════════════════════════════════════════════════════════════

    chat(client, agent.id,
         "Can you create a 4-week study plan to hit all three of my goals? "
         "Use your scratchpad to work it out, then finalize it in tasks.",
         show_tools=True)

    print("\nMemory after planning:")
    show_all_memory(client, agent.id)

    # ══════════════════════════════════════════════════════════════
    separator("STEP 6: Test RECALL memory — reference past conversation")
    # ══════════════════════════════════════════════════════════════

    chat(client, agent.id,
         "Hey, going back to our earlier conversation — "
         "what was that fine-tuning method you mentioned that works well on limited hardware?",
         show_tools=True)

    # ══════════════════════════════════════════════════════════════
    separator("STEP 7: Progress update (→ TASK MEMORY update)")
    # ══════════════════════════════════════════════════════════════

    chat(client, agent.id,
         "Quick update: I finished week 1! I've got a solid understanding of "
         "transformer attention now. Can you mark that goal as partially complete?")

    print("\nFinal memory state:")
    show_all_memory(client, agent.id)

    # ══════════════════════════════════════════════════════════════
    separator("SUMMARY: What each memory type did")
    # ══════════════════════════════════════════════════════════════

    print("""
  Memory Type   → What happened in this demo
  ───────────────────────────────────────────────────────────────
  human block   → Stored: name, profession, schedule, learning style
  tasks block   → Stored: goals, weekly plan, progress tracking
  scratchpad    → Used for planning, then content moved to tasks
  archival      → Pre-loaded knowledge base; searched by agent on query
  recall        → All messages auto-saved; searched when user said "earlier"
  ───────────────────────────────────────────────────────────────
  Together they give the agent PERFECT persistent memory across time.
    """)

    print(f"Agent ID: {agent.id}  (save this to continue the conversation later!)")
    return agent.id


if __name__ == "__main__":
    main()
