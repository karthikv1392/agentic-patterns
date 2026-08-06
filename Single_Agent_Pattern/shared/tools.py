"""Shared tool registry and executor.

Defines all tools available to agentic patterns, along with their
descriptions (used in LLM prompts) and implementations.

Tools
-----
calculator              — safely evaluate arithmetic expressions
get_datetime            — return current date / time info
search_knowledge_base   — keyword-search the local AI knowledge base
summarize_text          — LLM-powered text summarisation
generate_outline        — LLM-powered structured topic outline
"""

import ast
import datetime
import json
import math
import os
import platform
import re
from collections import Counter

from shared.llm import generate_response

# ---------------------------------------------------------------------------
# Tool descriptions shown to the LLM
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, dict] = {
    "calculator": {
        "name": "calculator",
        "description": (
            "Evaluates a mathematical expression and returns the numeric result. "
            "Use for arithmetic, percentages, compound interest, unit conversions, "
            "and any task requiring precise numeric computation."
        ),
        "parameters": {
            "expression": (
                "A valid Python arithmetic expression using only numbers and "
                "operators (+, -, *, /, **, %, //). "
                "Example: '(1500 * 0.15) + 1500'"
            )
        },
    },
    "get_datetime": {
        "name": "get_datetime",
        "description": (
            "Returns the current date, time, day of week, and platform info. "
            "Use when the task requires awareness of the current date or time."
        ),
        "parameters": {},
    },
    "search_knowledge_base": {
        "name": "search_knowledge_base",
        "description": (
            "Searches the local knowledge base about AI and agentic patterns "
            "and returns the most relevant passages. Use for questions about "
            "LLMs, RAG, prompt engineering, fine-tuning, tool use, memory, "
            "multi-agent systems, and related AI topics."
        ),
        "parameters": {
            "query": "The search query string.",
            "top_k": "Number of passages to return (integer, 1–5, default 3).",
        },
    },
    "summarize_text": {
        "name": "summarize_text",
        "description": (
            "Takes a piece of text and returns a concise LLM-generated summary. "
            "Use when the task requires condensing a large body of text."
        ),
        "parameters": {
            "text": "The text to summarize.",
            "max_words": "Target word count (integer, default 80).",
        },
    },
    "generate_outline": {
        "name": "generate_outline",
        "description": (
            "Generates a structured hierarchical outline for a given topic using "
            "an LLM. Use when the task requires organising information into "
            "sections and subsections before writing."
        ),
        "parameters": {
            "topic": "The topic or title to outline.",
            "depth": "Depth: 1 = top-level only, 2 = sections + subsections (default 2).",
        },
    },
}


def tool_descriptions_text() -> str:
    """Return a human-readable block describing all available tools."""
    lines = []
    for tool in TOOL_REGISTRY.values():
        lines.append(f"- **{tool['name']}**: {tool['description']}")
        for param, desc in tool.get("parameters", {}).items():
            lines.append(f"    - `{param}`: {desc}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Individual tool implementations
# ---------------------------------------------------------------------------

def _run_calculator(expression: str) -> str:
    _ALLOWED = {
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv,
        ast.USub, ast.UAdd,
    }
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        for node in ast.walk(tree):
            if type(node) not in _ALLOWED:
                return "Error: unsafe expression — only arithmetic operators are allowed."
        result = eval(compile(tree, "<string>", "eval"))  # noqa: S307
        return f"{expression} = {result}"
    except Exception as exc:
        return f"Error evaluating expression: {exc}"


def _run_get_datetime() -> str:
    now = datetime.datetime.now()
    return (
        f"Date:       {now.strftime('%Y-%m-%d')}\n"
        f"Time:       {now.strftime('%H:%M:%S')}\n"
        f"Day:        {now.strftime('%A')}\n"
        f"Week:       Week {now.strftime('%W')} of {now.year}\n"
        f"Platform:   {platform.system()} {platform.release()}"
    )


_KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.json")


def _kb_tokenize(text: str) -> list[str]:
    return re.findall(r"\b[a-z]+\b", text.lower())


def _kb_score(query_tokens: list[str], chunk_text: str) -> float:
    tokens = _kb_tokenize(chunk_text)
    if not tokens:
        return 0.0
    tf = Counter(tokens)
    total = len(tokens)
    return sum(math.log(1.0 + 10.0 * tf.get(t, 0) / total) for t in set(query_tokens))


def _run_search_knowledge_base(query: str, top_k: int = 3) -> str:
    with open(_KB_PATH, "r", encoding="utf-8") as f:
        kb = json.load(f)
    query_tokens = _kb_tokenize(query)
    scored = sorted(
        [(chunk, _kb_score(query_tokens, chunk["title"] + " " + chunk["content"])) for chunk in kb],
        key=lambda x: x[1], reverse=True,
    )
    results = [chunk for chunk, score in scored[:top_k] if score > 0]
    if not results:
        return "No relevant passages found in the knowledge base."
    return "\n\n".join(f"[{i+1}] {c['title']}\n{c['content']}" for i, c in enumerate(results))


def _run_summarize_text(text: str, max_words: int = 80) -> str:
    prompt = (
        f"Summarize the following text in no more than {max_words} words. "
        "Return just the summary, no preamble.\n\n" + text
    )
    return generate_response(prompt)


def _run_generate_outline(topic: str, depth: int = 2) -> str:
    depth_instruction = (
        "top-level sections only" if depth == 1
        else "sections with subsections (2 levels)"
    )
    prompt = (
        f"Generate a structured hierarchical outline for: '{topic}'.\n"
        f"Include {depth_instruction}. Use markdown headings. "
        "Return only the outline."
    )
    return generate_response(prompt)


# ---------------------------------------------------------------------------
# Unified executor
# ---------------------------------------------------------------------------

def execute_tool(tool_name: str, parameters: dict) -> str:
    """Dispatch a tool call and return the string result."""
    if tool_name == "calculator":
        return _run_calculator(parameters.get("expression", ""))
    if tool_name == "get_datetime":
        return _run_get_datetime()
    if tool_name == "search_knowledge_base":
        return _run_search_knowledge_base(
            parameters.get("query", ""), int(parameters.get("top_k", 3))
        )
    if tool_name == "summarize_text":
        return _run_summarize_text(
            parameters.get("text", ""), int(parameters.get("max_words", 80))
        )
    if tool_name == "generate_outline":
        return _run_generate_outline(
            parameters.get("topic", ""), int(parameters.get("depth", 2))
        )
    return f"Unknown tool: '{tool_name}'. Available: {list(TOOL_REGISTRY.keys())}"
