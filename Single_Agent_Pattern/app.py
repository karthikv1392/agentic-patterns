"""Agentic Patterns — Streamlit UI

A visual, interactive tour through 8 single-agent patterns that progress
from simple LLM calls to full multi-path planning with tool use.
"""

import json
import streamlit as st

# ---------------------------------------------------------------------------
# Pattern imports — each pattern lives in its own folder under patterns/
# ---------------------------------------------------------------------------
from patterns.p01_passive_goal_creator.agent   import run as run_passive
from patterns.p02_proactive_goal_creator.agent import run as run_proactive
from patterns.p03_prompt_optimizer.agent       import run as run_optimizer
from patterns.p04_rag.agent                    import run as run_rag
from patterns.p05_one_step_tool_agent.agent    import run as run_one_step
from patterns.p06_incremental_tool_agent.agent import run as run_incremental
from patterns.p07_single_path_plan.agent       import run as run_single_path
from patterns.p08_multi_path_plan.agent        import run as run_multi_path
from patterns.p09_self_reflection.agent        import run as run_self_reflection
from shared.tools                              import tool_descriptions_text, TOOL_REGISTRY

# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------
PATTERNS = {
    "01 · Passive Goal Creator": {
        "description": "Plain prompt → sub-task breakdown → final answer. Pure LLM, no tools, no extra context.",
        "complexity": "Beginner",
        "llm_calls": 2,
        "uses_tools": False,
        "folder": "patterns/p01_passive_goal_creator/",
        "files": ["agent.py"],
        "placeholder": "e.g. Create a travel itinerary for 3 days in Tokyo",
        "input_type": "goal",
    },
    "02 · Proactive Goal Creator": {
        "description": "Enriches the goal with live environmental context (date, time, platform) and optional image analysis before calling the LLM.",
        "complexity": "Beginner",
        "llm_calls": 2,
        "uses_tools": False,
        "folder": "patterns/p02_proactive_goal_creator/",
        "files": ["context.py", "agent.py"],
        "placeholder": "e.g. What should I focus on today to be productive?",
        "input_type": "goal+image",
    },
    "03 · Prompt Optimizer": {
        "description": "A first LLM call rewrites the user's rough prompt to be clearer and more specific. The optimised prompt is then used for the actual task.",
        "complexity": "Beginner",
        "llm_calls": 2,
        "uses_tools": False,
        "folder": "patterns/p03_prompt_optimizer/",
        "files": ["optimizer.py", "agent.py"],
        "placeholder": "e.g. Tell me about machine learning",
        "input_type": "prompt",
    },
    "04 · RAG": {
        "description": "Retrieves relevant chunks from a local knowledge base using keyword scoring, then injects them as context into the LLM prompt to ground the answer.",
        "complexity": "Intermediate",
        "llm_calls": 1,
        "uses_tools": True,
        "folder": "patterns/p04_rag/",
        "files": ["retriever.py", "agent.py"],
        "placeholder": "e.g. What is RAG and how does it reduce hallucinations?",
        "input_type": "query",
    },
    "05 · One-Step Tool Agent": {
        "description": "A single LLM call produces a plan AND selects the best tool + parameters (as JSON). The tool runs, then the LLM synthesises the final answer.",
        "complexity": "Intermediate",
        "llm_calls": 2,
        "uses_tools": True,
        "folder": "patterns/p05_one_step_tool_agent/",
        "files": ["agent.py"],
        "placeholder": "e.g. What is 18% tip on $84.50 split 4 ways?",
        "input_type": "goal",
    },
    "06 · Incremental Tool Agent": {
        "description": "Three sequential LLM calls build on each other — analysis → tool selection → exact parameters — before the tool runs and a final answer is synthesised.",
        "complexity": "Intermediate",
        "llm_calls": 4,
        "uses_tools": True,
        "folder": "patterns/p06_incremental_tool_agent/",
        "files": ["agent.py"],
        "placeholder": "e.g. Explain what RAG is and how it reduces hallucinations",
        "input_type": "goal",
    },
    "07 · Single Path Plan": {
        "description": "Generates a linear 4-6 step plan. Each step decides whether to call a tool, runs it if needed, then produces step output. All steps synthesised at the end.",
        "complexity": "Advanced",
        "llm_calls": "2N + 2",
        "uses_tools": True,
        "folder": "patterns/p07_single_path_plan/",
        "files": ["planner.py", "executor.py", "agent.py"],
        "placeholder": "e.g. Write a beginner's guide to learning Python programming",
        "input_type": "goal",
    },
    "08 · Multi-Path Plan": {
        "description": "Each step has 2-3 alternative approaches. A dedicated evaluator picks the best option per step. The chosen path is then executed (with tool use) and synthesised.",
        "complexity": "Advanced",
        "llm_calls": "4N + 2",
        "uses_tools": True,
        "folder": "patterns/p08_multi_path_plan/",
        "files": ["planner.py", "evaluator.py", "executor.py", "agent.py"],
        "placeholder": "e.g. Design a marketing strategy for a new mobile app",
        "input_type": "goal",
    },
    "09 · Self-Reflection": {
        "description": "The agent drafts a plan (with tool selections), then reflects on its own choices — checking approach, tool fit, and logic — before revising and executing the final plan.",
        "complexity": "Advanced",
        "llm_calls": "3N + 2",
        "uses_tools": True,
        "folder": "patterns/p09_self_reflection/",
        "files": ["planner.py", "reflector.py", "executor.py", "agent.py"],
        "placeholder": "e.g. Build a study plan for learning data science in 3 months",
        "input_type": "goal",
    },
}

COMPLEXITY_COLOR = {"Beginner": "#22c55e", "Intermediate": "#f59e0b", "Advanced": "#ef4444"}

# ---------------------------------------------------------------------------
# Page config & global CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Agentic Patterns",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Sidebar ───────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1b4b 0%, #312e81 60%, #1e3a5f 100%);
}
[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
[data-testid="stSidebar"] .stRadio label {
    padding: 6px 10px;
    border-radius: 8px;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.12);
}

/* ── Pattern header card ───────────────────────────────── */
/* Light background tint so it reads on both white and grey Streamlit themes */
.pattern-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(124,58,237,0.08) 100%);
    border: 1.5px solid rgba(99,102,241,0.45);
    border-left: 5px solid #6366f1;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.5rem;
}
/* Let the text inherit the theme colour so it's readable in both modes */
.pattern-card p { color: inherit; margin: 0.5rem 0 0 0; font-size: 0.95rem; opacity: 0.85; }

/* ── Complexity / stat badges ──────────────────────────── */
/* Use 700-series colours — WCAG AA contrast on white (≥4.5:1) */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-right: 6px;
}
.badge-green  { background: #dcfce7; color: #15803d; border: 1.5px solid #16a34a; }
.badge-yellow { background: #fef3c7; color: #b45309; border: 1.5px solid #d97706; }
.badge-red    { background: #fee2e2; color: #b91c1c; border: 1.5px solid #dc2626; }
.badge-blue   { background: #dbeafe; color: #1d4ed8; border: 1.5px solid #2563eb; }
.badge-purple { background: #ede9fe; color: #6d28d9; border: 1.5px solid #7c3aed; }

/* ── Section labels ────────────────────────────────────── */
.section-label {
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4b5563;
    margin: 1.5rem 0 0.5rem 0;
}

/* ── Step row ──────────────────────────────────────────── */
.step-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 6px;
}
.step-circle {
    flex-shrink: 0;
    width: 34px; height: 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #7c3aed);
    color: #fff;
    font-weight: 700;
    font-size: 15px;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 12px rgba(99,102,241,0.45);
}
/* Inherit theme colour so it's readable in light and dark modes */
.step-text { padding-top: 5px; color: inherit; font-size: 0.9rem; }

/* ── Tool tag ──────────────────────────────────────────── */
/* White text on a vivid gradient — always readable regardless of theme */
.tool-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    background: linear-gradient(135deg, #7c3aed, #db2777);
    color: #fff;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-left: 8px;
    vertical-align: middle;
}
.no-tool-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #cbd5e1;
    font-size: 0.72rem;
    font-weight: 600;
    margin-left: 8px;
    vertical-align: middle;
}

/* ── File structure ────────────────────────────────────── */
.file-tree {
    background: #1e1b4b;
    border: 1px solid rgba(165,180,252,0.25);
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    font-family: monospace;
    font-size: 0.82rem;
    /* explicit colours since bg is always dark */
    color: #a5b4fc;
    line-height: 1.7;
}
/* File tree always has dark bg, so these bright colours are fine */
.file-tree .folder { color: #93c5fd; }
.file-tree .pyfile { color: #c4b5fd; }
.file-tree .shared { color: #6ee7b7; }

/* ── Final output card ─────────────────────────────────── */
.final-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.07), rgba(124,58,237,0.07));
    border: 1.5px solid rgba(99,102,241,0.5);
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 0.5rem;
}

/* ── Option cards in multi-path ────────────────────────── */
.opt-selected {
    background: #f0fdf4;
    border: 1.5px solid #16a34a;
    border-radius: 8px;
    padding: 8px 14px;
    margin: 4px 0;
    color: #14532d;
}
.opt-normal {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 14px;
    margin: 4px 0;
    color: #475569;
}

/* ── Self-reflection cards ─────────────────────────────── */
.reflect-sound {
    background: #f0fdf4;
    border: 1.5px solid #16a34a;
    border-left: 5px solid #16a34a;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 0.75rem;
    color: #14532d;
}
.reflect-revised {
    background: #fefce8;
    border: 1.5px solid #ca8a04;
    border-left: 5px solid #ca8a04;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 0.75rem;
    color: #713f12;
}
.reflect-issue {
    background: #fff7ed;
    border: 1px solid #fb923c;
    border-radius: 8px;
    padding: 6px 12px;
    margin: 4px 0;
    color: #7c2d12;
    font-size: 0.88rem;
}
.plan-step-initial {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 5px 0;
    color: #334155;
}
.plan-step-revised {
    background: #fefce8;
    border: 1.5px solid #ca8a04;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 5px 0;
    color: #713f12;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _complexity_badge(c: str) -> str:
    cls = {"Beginner": "green", "Intermediate": "yellow", "Advanced": "red"}.get(c, "blue")
    return f'<span class="badge badge-{cls}">{c}</span>'


def _badge(text: str, cls: str = "blue") -> str:
    return f'<span class="badge badge-{cls}">{text}</span>'


def _tool_tag(tool: str | None) -> str:
    if tool:
        return f'<span class="tool-tag">🔧 {tool}</span>'
    return '<span class="no-tool-tag">no tool</span>'


def _show_pattern_header(name: str, meta: dict):
    llm = meta["llm_calls"]
    tools_badge = _badge("uses tools", "purple") if meta["uses_tools"] else _badge("LLM only", "blue")
    st.markdown(f"""
<div class="pattern-card">
  <div>
    {_complexity_badge(meta['complexity'])}
    {tools_badge}
    {_badge(f"~{llm} LLM calls", "blue")}
  </div>
  <p>{meta['description']}</p>
</div>""", unsafe_allow_html=True)


def _show_file_structure(meta: dict):
    folder = meta["folder"]
    files  = meta["files"]
    lines  = [f'<span class="folder">📁 {folder}</span>']
    for f in files:
        lines.append(f'&nbsp;&nbsp;&nbsp;&nbsp;<span class="pyfile">🐍 {f}</span>')
    lines += [
        '<span class="shared">📁 shared/</span>',
        '&nbsp;&nbsp;&nbsp;&nbsp;<span class="shared">🐍 llm.py</span>',
    ]
    if meta["uses_tools"]:
        lines.append('&nbsp;&nbsp;&nbsp;&nbsp;<span class="shared">🐍 tools.py</span>')
    st.markdown(
        '<div class="file-tree">' + "<br>".join(lines) + "</div>",
        unsafe_allow_html=True,
    )


def _show_step_list(plan_steps: list[dict], key_field: str = "description"):
    for step in plan_steps:
        num  = step.get("step_number", "?")
        desc = step.get(key_field, step.get("description", step.get("goal", "")))
        st.markdown(f"""
<div class="step-row">
  <div class="step-circle">{num}</div>
  <div class="step-text">{desc}</div>
</div>""", unsafe_allow_html=True)


def _show_step_output(s: dict, label_field: str = "description"):
    label      = s.get(label_field, s.get("goal", s.get("description", "")))
    tool_used  = s.get("tool_used")
    tool_out   = s.get("tool_output")
    step_num   = s.get("step_number", "?")
    approach   = s.get("chosen_approach", "")

    title = f"Step {step_num} — {label}"
    if approach:
        title += f" · *{approach}*"

    with st.expander(title):
        if tool_used:
            st.markdown(
                f'Tool invoked: {_tool_tag(tool_used)}',
                unsafe_allow_html=True,
            )
            st.code(tool_out, language="text")
            st.divider()
        else:
            st.markdown(_tool_tag(None), unsafe_allow_html=True)
            st.divider()
        st.markdown(s["output"])


def _show_tools_expander():
    with st.expander("🛠 Available Tools"):
        for name, t in TOOL_REGISTRY.items():
            with st.container(border=True):
                st.markdown(f"**`{name}`** — {t['description']}")
                if t.get("parameters"):
                    for p, d in t["parameters"].items():
                        st.markdown(f"&nbsp;&nbsp;• `{p}`: {d}", unsafe_allow_html=True)


def _final_output_card(text: str):
    st.markdown('<div class="section-label">Final Output</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(text)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
<div style="padding:1.2rem 0 0.5rem 0;">
  <div style="font-size:1.3rem;font-weight:900;color:#ffffff;letter-spacing:-0.01em;
              text-shadow:0 2px 8px rgba(0,0,0,0.5);">
    🤖 Agentic Patterns
  </div>
  <div style="font-size:0.8rem;color:#c7d2fe;margin-top:4px;font-weight:500;">
    9 patterns · beginner → advanced
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("---")
    selected = st.radio("Select a pattern", list(PATTERNS.keys()), label_visibility="collapsed")
    st.markdown("---")
    meta = PATTERNS[selected]
    c = meta["complexity"]
    color = COMPLEXITY_COLOR[c]
    st.markdown(f'<span style="color:{color};font-weight:700;font-size:0.8rem;">⬤ {c}</span>', unsafe_allow_html=True)
    st.caption(meta["description"])
    st.markdown("---")
    st.caption("📁 File structure")
    _show_file_structure(meta)

# ---------------------------------------------------------------------------
# App banner
# ---------------------------------------------------------------------------
st.markdown("""
<div style="background:linear-gradient(135deg,#312e81 0%,#1e3a5f 50%,#1e1b4b 100%);
            padding:2rem 2.5rem;border-radius:16px;margin-bottom:1.5rem;
            box-shadow:0 8px 32px rgba(49,46,129,0.35);
            border:1px solid rgba(165,180,252,0.25);overflow:hidden;">
  <div style="color:#ffffff;font-size:2rem;font-weight:900;line-height:1.2;
              margin:0 0 0.5rem 0;letter-spacing:-0.02em;">
    🤖 Agentic Patterns
  </div>
  <div style="color:#c7d2fe;font-size:1rem;line-height:1.5;margin:0;">
    An interactive tour through 9 agent patterns — from simple LLM calls
    to self-reflecting agents with tool use. Each pattern lives in its own folder
    so you can study the code structure alongside the live demo.
  </div>
</div>
""", unsafe_allow_html=True)

meta = PATTERNS[selected]
st.markdown(f"### {selected}")
_show_pattern_header(selected, meta)

# ---------------------------------------------------------------------------
# Pattern UIs
# ---------------------------------------------------------------------------

# ── 01 Passive Goal Creator ────────────────────────────────────────────────
if selected == "01 · Passive Goal Creator":
    user_prompt = st.text_area("Goal / Task", placeholder=meta["placeholder"], height=90)
    if st.button("▶ Run", type="primary"):
        if not user_prompt.strip():
            st.warning("Please enter a goal.")
        else:
            with st.spinner("Analysing goal and generating response…"):
                result = run_passive(user_prompt)

            st.markdown('<div class="section-label">Sub-task Breakdown</div>', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(result["goal_analysis"])
            _final_output_card(result["final_output"])

# ── 02 Proactive Goal Creator ──────────────────────────────────────────────
elif selected == "02 · Proactive Goal Creator":
    user_prompt   = st.text_area("Goal / Task", placeholder=meta["placeholder"], height=90)
    uploaded_file = st.file_uploader("Upload an image (optional)", type=["png","jpg","jpeg","webp"])
    if st.button("▶ Run", type="primary"):
        if not user_prompt.strip():
            st.warning("Please enter a goal.")
        else:
            image_bytes = uploaded_file.read() if uploaded_file else None
            with st.spinner("Gathering context and generating response…"):
                result = run_proactive(user_prompt, image_bytes=image_bytes)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-label">Environmental Context</div>', unsafe_allow_html=True)
                st.code(result["env_context"], language="yaml")
            with col2:
                if result["image_analysis"]:
                    st.markdown('<div class="section-label">Image Analysis</div>', unsafe_allow_html=True)
                    with st.container(border=True):
                        st.markdown(result["image_analysis"])
            _final_output_card(result["final_output"])

# ── 03 Prompt Optimizer ────────────────────────────────────────────────────
elif selected == "03 · Prompt Optimizer":
    user_prompt = st.text_area("Your rough prompt", placeholder=meta["placeholder"], height=90)
    if st.button("▶ Run", type="primary"):
        if not user_prompt.strip():
            st.warning("Please enter a prompt.")
        else:
            with st.spinner("Optimising prompt…"):
                result = run_optimizer(user_prompt)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-label">Original Prompt</div>', unsafe_allow_html=True)
                st.info(result["original_prompt"])
            with col2:
                st.markdown('<div class="section-label">Optimised Prompt</div>', unsafe_allow_html=True)
                st.success(result["optimized_prompt"])
            _final_output_card(result["final_output"])

# ── 04 RAG ─────────────────────────────────────────────────────────────────
elif selected == "04 · RAG":
    user_query = st.text_area("Your question", placeholder=meta["placeholder"], height=90)
    top_k = st.slider("Chunks to retrieve", 1, 5, 3)
    if st.button("▶ Run", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Retrieving context and generating response…"):
                result = run_rag(user_query, top_k=top_k)

            chunks = result["retrieved_chunks"]
            st.markdown(
                f'<div class="section-label">Retrieved Context '
                f'({_badge(f"{len(chunks)} chunk(s)", "purple")})</div>',
                unsafe_allow_html=True,
            )
            if chunks:
                for i, c in enumerate(chunks, 1):
                    with st.expander(f"[{i}] {c['title']}"):
                        st.markdown(c["content"])
            else:
                st.warning("No relevant chunks found — answering from model knowledge.")
            _final_output_card(result["final_output"])

# ── 05 One-Step Tool Agent ─────────────────────────────────────────────────
elif selected == "05 · One-Step Tool Agent":
    _show_tools_expander()
    user_goal = st.text_area("Goal", placeholder=meta["placeholder"], height=90)
    if st.button("▶ Run", type="primary"):
        if not user_goal.strip():
            st.warning("Please enter a goal.")
        else:
            with st.spinner("Planning and executing…"):
                result = run_one_step(user_goal)

            st.markdown('<div class="section-label">Plan</div>', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(result["plan"])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="section-label">Tool Selected</div>', unsafe_allow_html=True)
                st.markdown(_tool_tag(result["selected_tool"]), unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="section-label">Parameters</div>', unsafe_allow_html=True)
                st.code(json.dumps(result["tool_parameters"], indent=2), language="json")
            with col3:
                st.markdown('<div class="section-label">Reasoning</div>', unsafe_allow_html=True)
                st.caption(result["reasoning"])

            st.markdown('<div class="section-label">Tool Output</div>', unsafe_allow_html=True)
            st.code(result["tool_output"], language="text")
            _final_output_card(result["final_output"])

# ── 06 Incremental Tool Agent ──────────────────────────────────────────────
elif selected == "06 · Incremental Tool Agent":
    _show_tools_expander()
    user_goal = st.text_area("Goal", placeholder=meta["placeholder"], height=90)
    if st.button("▶ Run", type="primary"):
        if not user_goal.strip():
            st.warning("Please enter a goal.")
        else:
            with st.spinner("Running 3 reasoning rounds…"):
                result = run_incremental(user_goal)

            st.markdown('<div class="section-label">Incremental Reasoning Rounds</div>', unsafe_allow_html=True)
            for r in result["rounds"]:
                with st.expander(f"Round {r['round']} — {r['label']}"):
                    st.markdown(r["response"])

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-label">Tool Selected</div>', unsafe_allow_html=True)
                st.markdown(_tool_tag(result["selected_tool"]), unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="section-label">Parameters</div>', unsafe_allow_html=True)
                st.code(json.dumps(result["tool_parameters"], indent=2), language="json")

            st.markdown('<div class="section-label">Tool Output</div>', unsafe_allow_html=True)
            st.code(result["tool_output"], language="text")
            _final_output_card(result["final_output"])

# ── 07 Single Path Plan ────────────────────────────────────────────────────
elif selected == "07 · Single Path Plan":
    _show_tools_expander()
    user_goal = st.text_area("Goal", placeholder=meta["placeholder"], height=90)
    if st.button("▶ Run", type="primary"):
        if not user_goal.strip():
            st.warning("Please enter a goal.")
        else:
            with st.spinner("Generating plan and executing steps…"):
                result = run_single_path(user_goal)

            st.markdown('<div class="section-label">Generated Plan</div>', unsafe_allow_html=True)
            with st.container(border=True):
                _show_step_list(result["plan_steps"])

            tools_used = [s["tool_used"] for s in result["step_outputs"] if s["tool_used"]]
            c1, c2, c3 = st.columns(3)
            c1.metric("Steps", len(result["step_outputs"]))
            c2.metric("Tools Invoked", len(tools_used))
            c3.metric("Tools Used", ", ".join(set(tools_used)) or "none")

            st.markdown('<div class="section-label">Step-by-Step Execution</div>', unsafe_allow_html=True)
            for s in result["step_outputs"]:
                _show_step_output(s)
            _final_output_card(result["final_output"])

# ── 08 Multi-Path Plan ─────────────────────────────────────────────────────
elif selected == "08 · Multi-Path Plan":
    _show_tools_expander()
    user_goal = st.text_area("Goal", placeholder=meta["placeholder"], height=90)
    if st.button("▶ Run", type="primary"):
        if not user_goal.strip():
            st.warning("Please enter a goal.")
        else:
            with st.spinner("Generating multi-path plan, evaluating options, and executing…"):
                result = run_multi_path(user_goal)

            st.markdown('<div class="section-label">Plan · Options · Selected Paths</div>', unsafe_allow_html=True)
            for step, ev in zip(result["plan_steps"], result["evaluations"]):
                with st.expander(f"Step {step['step_number']} — {step['goal']}"):
                    for opt in step.get("options", []):
                        chosen = opt["id"] == ev["chosen_option_id"]
                        div_cls = "opt-selected" if chosen else "opt-normal"
                        check   = " ✓ <strong>SELECTED</strong>" if chosen else ""
                        st.markdown(
                            f'<div class="{div_cls}">'
                            f'<strong>[{opt["id"]}] {opt["approach"]}</strong>{check}<br>'
                            f'<span style="font-size:0.85rem;">{opt["description"]}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    st.info(f"**Rationale:** {ev['rationale']}")

            tools_used = [s["tool_used"] for s in result["step_outputs"] if s["tool_used"]]
            c1, c2, c3 = st.columns(3)
            c1.metric("Steps", len(result["step_outputs"]))
            c2.metric("Tools Invoked", len(tools_used))
            c3.metric("Tools Used", ", ".join(set(tools_used)) or "none")

            st.markdown('<div class="section-label">Step Execution Outputs</div>', unsafe_allow_html=True)
            for s in result["step_outputs"]:
                _show_step_output(s, label_field="goal")
            _final_output_card(result["final_output"])

# ── 09 Self-Reflection ─────────────────────────────────────────────────────
elif selected == "09 · Self-Reflection":
    _show_tools_expander()
    user_goal = st.text_area("Goal", placeholder=meta["placeholder"], height=90)
    if st.button("▶ Run", type="primary"):
        if not user_goal.strip():
            st.warning("Please enter a goal.")
        else:
            with st.spinner("Planning → Reflecting → Executing…"):
                result = run_self_reflection(user_goal)

            ref = result["reflection"]

            # ── Initial plan ──────────────────────────────────────────────
            st.markdown('<div class="section-label">Initial Plan (before reflection)</div>',
                        unsafe_allow_html=True)
            for step in result["initial_plan"]:
                tool_label = (
                    f'<span class="tool-tag">🔧 {step["tool_name"]}</span>'
                    if step.get("tool_name") else
                    '<span class="no-tool-tag">no tool</span>'
                )
                st.markdown(
                    f'<div class="plan-step-initial">'
                    f'<strong>Step {step["step_number"]}: {step["goal"]}</strong>'
                    f'&nbsp;&nbsp;{tool_label}<br>'
                    f'<span style="font-size:0.85rem;">Approach: {step["approach"]}</span><br>'
                    f'<span style="font-size:0.8rem;opacity:0.75;">Reasoning: {step.get("reasoning","")}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Reflection ────────────────────────────────────────────────
            st.markdown('<div class="section-label">Reflection</div>', unsafe_allow_html=True)
            if ref["is_sound"] and not ref["changes_made"]:
                st.markdown(
                    '<div class="reflect-sound">'
                    '<strong>✓ Plan is sound</strong> — no changes needed.'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="reflect-revised">'
                    '<strong>⚠ Issues found — plan revised</strong>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                if ref["issues"]:
                    st.markdown("**Issues identified:**")
                    for issue in ref["issues"]:
                        st.markdown(
                            f'<div class="reflect-issue">• {issue}</div>',
                            unsafe_allow_html=True,
                        )

            with st.expander("📝 Full Reflection Text"):
                st.markdown(ref["reflection_text"])

            # ── Revised / final plan ──────────────────────────────────────
            if ref["changes_made"]:
                st.markdown('<div class="section-label">Revised Plan (after reflection)</div>',
                            unsafe_allow_html=True)
                for step in result["final_plan"]:
                    tool_label = (
                        f'<span class="tool-tag">🔧 {step["tool_name"]}</span>'
                        if step.get("tool_name") else
                        '<span class="no-tool-tag">no tool</span>'
                    )
                    st.markdown(
                        f'<div class="plan-step-revised">'
                        f'<strong>Step {step["step_number"]}: {step["goal"]}</strong>'
                        f'&nbsp;&nbsp;{tool_label}<br>'
                        f'<span style="font-size:0.85rem;">Approach: {step["approach"]}</span><br>'
                        f'<span style="font-size:0.8rem;opacity:0.75;">Reasoning: {step.get("reasoning","")}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # ── Metrics ───────────────────────────────────────────────────
            tools_used = [s["tool_used"] for s in result["step_outputs"] if s["tool_used"]]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Steps", len(result["step_outputs"]))
            c2.metric("Tools Invoked", len(tools_used))
            c3.metric("Tools Used", ", ".join(set(tools_used)) or "none")
            c4.metric("Plan Revised?", "Yes" if ref["changes_made"] else "No")

            # ── Step execution outputs ────────────────────────────────────
            st.markdown('<div class="section-label">Step Execution Outputs</div>',
                        unsafe_allow_html=True)
            for s in result["step_outputs"]:
                _show_step_output(s, label_field="goal")

            _final_output_card(result["final_output"])
