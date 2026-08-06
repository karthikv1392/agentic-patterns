"""
app.py - MemGPT Memory Demo UI (Streamlit)
==========================================
Run: streamlit run app.py

Shows a chat interface on the left and a live Memory Inspector on the right.
Every time the agent updates a memory block, the right panel refreshes instantly.
"""

import json
import streamlit as st
from config import get_client, DEFAULT_MODEL, DEFAULT_EMBEDDING

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MemGPT Memory Demo",
    page_icon="🧠",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.tool-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-family: monospace;
    margin: 2px 2px;
}
.badge-memory  { background:#fff3e0; color:#e65100; border:1px solid #ffcc80; }
.badge-search  { background:#e3f2fd; color:#1565c0; border:1px solid #90caf9; }
.badge-archival{ background:#f3e5f5; color:#6a1b9a; border:1px solid #ce93d8; }
.badge-other   { background:#f5f5f5; color:#424242; border:1px solid #e0e0e0; }
.block-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #888;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_client():
    return get_client()


def create_agent(client):
    agent = client.agents.create(
        name="demo-agent",
        model=DEFAULT_MODEL,
        embedding=DEFAULT_EMBEDDING,
        memory_blocks=[
            {
                "label": "persona",
                "value": (
                    "I am Sage, a helpful personal assistant with perfect memory. "
                    "I always update my memory blocks when I learn something new about the user. "
                    "I use the scratchpad for working notes on complex tasks."
                ),
            },
            {"label": "human",      "value": "No information about this user yet."},
            {"label": "tasks",      "value": "No active tasks yet."},
            {"label": "scratchpad", "value": "[empty]"},
        ],
    )
    return agent.id


def fetch_blocks(client, agent_id: str) -> dict:
    """Return current values of all interesting memory blocks."""
    blocks = {}
    for label in ["human", "tasks", "scratchpad"]:
        try:
            b = client.agents.blocks.retrieve(agent_id=agent_id, block_label=label)
            blocks[label] = b.value
        except Exception:
            blocks[label] = "(unavailable)"
    return blocks


def count_recall(client, agent_id: str) -> int:
    """Count user messages in recall storage."""
    try:
        count = 0
        for msg in client.agents.messages.list(agent_id=agent_id):
            if getattr(msg, "message_type", "") == "user_message":
                count += 1
        return count
    except Exception:
        return 0


def tool_badge(name: str, args_str: str) -> str:
    """Return an HTML badge for a tool call."""
    try:
        args = json.loads(args_str)
        label = args.get("label", args.get("query", ""))
        detail = f"({label})" if label else ""
    except Exception:
        detail = ""

    if "memory" in name and "archival" not in name:
        cls = "badge-memory"
        icon = "🔧"
    elif "conversation" in name or "recall" in name:
        cls = "badge-search"
        icon = "🔍"
    elif "archival" in name:
        cls = "badge-archival"
        icon = "📦"
    else:
        cls = "badge-other"
        icon = "⚙️"

    return f'<span class="tool-badge {cls}">{icon} {name}{detail}</span>'


def send_message(client, agent_id: str, user_text: str):
    """
    Send a message to the agent and return:
      (assistant_text: str, tool_badges_html: str)
    """
    resp = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": user_text}],
    )

    assistant_text = ""
    badges_html = ""

    for msg in resp.messages:
        mtype = getattr(msg, "message_type", "")
        if mtype == "tool_call_message":
            name = msg.tool_call.name
            args = msg.tool_call.arguments or ""
            badges_html += tool_badge(name, args)
        elif mtype == "assistant_message":
            assistant_text += msg.content

    return assistant_text, badges_html


# ── Session state init ────────────────────────────────────────────────────────

if "client" not in st.session_state:
    st.session_state.client = make_client()

if "agent_id" not in st.session_state:
    with st.spinner("Creating agent..."):
        st.session_state.agent_id = create_agent(st.session_state.client)
    st.session_state.messages = []   # [{role, content, badges_html}]

client   = st.session_state.client
agent_id = st.session_state.agent_id

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_reset = st.columns([5, 1])
with col_title:
    st.title("🧠 MemGPT Memory Demo")
    st.caption(f"Agent: `{agent_id}` · Model: `{DEFAULT_MODEL}`")
with col_reset:
    st.write("")
    if st.button("🔄 Reset", use_container_width=True):
        for key in ["agent_id", "messages", "client"]:
            st.session_state.pop(key, None)
        st.rerun()

st.divider()

# ── Two-column layout ─────────────────────────────────────────────────────────
chat_col, mem_col = st.columns([3, 2], gap="large")

# ── RIGHT: Memory Inspector ───────────────────────────────────────────────────
with mem_col:
    st.subheader("Memory Inspector")
    blocks      = fetch_blocks(client, agent_id)
    recall_count = count_recall(client, agent_id)

    BLOCK_META = {
        "human":      ("👤 User Memory",   "What the agent knows about you"),
        "tasks":      ("✅ Task Memory",   "Goals and to-dos"),
        "scratchpad": ("📝 Scratchpad",    "Agent working notes"),
    }

    for label, (title, desc) in BLOCK_META.items():
        with st.expander(title, expanded=True):
            st.caption(desc)
            val = blocks.get(label, "(empty)")
            st.code(val, language=None)

    with st.expander("🕒 Recall Memory", expanded=True):
        st.caption("Full conversation history (auto-saved)")
        st.metric("Messages in history", recall_count)
        st.caption("Agent searches this with `conversation_search` when you reference past chats.")

    with st.expander("📦 Archival Memory (RAG)", expanded=False):
        st.caption("Long-term vector storage — requires OpenAI embeddings in local Docker build.")
        st.info(
            "Archival/RAG is skipped in this local setup.\n\n"
            "To enable: add `OPENAI_API_KEY` to your Docker run command.\n\n"
            "The agent still uses recall + core memory fully.",
            icon="ℹ️",
        )

# ── LEFT: Chat ────────────────────────────────────────────────────────────────
with chat_col:
    st.subheader("Chat")

    # Render history
    for turn in st.session_state.messages:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn.get("badges_html"):
                st.markdown(turn["badges_html"], unsafe_allow_html=True)

    # Input
    if user_input := st.chat_input("Type a message..."):

        # Show user message immediately
        st.session_state.messages.append({"role": "user", "content": user_input, "badges_html": ""})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply, badges = send_message(client, agent_id, user_input)
            st.markdown(reply)
            if badges:
                st.markdown(badges, unsafe_allow_html=True)

        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "badges_html": badges,
        })

        # Rerun so memory inspector refreshes
        st.rerun()
