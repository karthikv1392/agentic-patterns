"""Synthesiser — collects all parallel agent outputs and aggregates them.

Three aggregation strategies
-----------------------------
merge      — Weave all outputs into one comprehensive, unified document.
             Best when sub-tasks cover complementary dimensions.

summarise  — Distil the most important insights from each agent into a
             concise, executive-style summary.
             Best when brevity matters more than completeness.

vote       — An LLM reads all outputs and selects the single best one,
             explaining why it wins over the others.
             Best when sub-tasks are comparable alternatives.
"""

import json
import re

from shared.llm import generate_response


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def _format_results_block(results: list[dict]) -> str:
    lines = []
    for r in results:
        lines.append(
            f"--- {r['agent_name']} | Sub-task: {r['sub_task_title']} ---"
        )
        lines.append(r["output"])
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Aggregation modes
# ---------------------------------------------------------------------------

def _synthesise_merge(task: str, results: list[dict]) -> dict:
    """Merge all outputs into one comprehensive unified document."""
    block = _format_results_block(results)
    prompt = (
        "You are a synthesis expert. Multiple specialist agents tackled different "
        "dimensions of the same task in parallel. Merge their outputs into one "
        "comprehensive, well-structured final answer. Remove redundancy, highlight "
        "complementary insights, and produce a coherent document.\n\n"
        f"Original task:\n{task}\n\n"
        f"Specialist outputs:\n{block}\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "final_answer": "merged content in markdown",\n'
        '  "key_themes": ["theme1", "theme2", "theme3"],\n'
        '  "reasoning": "brief note on how you merged the outputs"\n'
        "}"
    )
    raw = generate_response(prompt)
    data = _extract_json(raw)
    return {
        "mode": "merge",
        "final_answer": data.get("final_answer", raw),
        "key_themes": data.get("key_themes", []),
        "reasoning": data.get("reasoning", ""),
        "winner": None,
    }


def _synthesise_summarise(task: str, results: list[dict]) -> dict:
    """Distil the most important insights into a concise executive summary."""
    block = _format_results_block(results)
    prompt = (
        "You are a synthesis expert. Multiple specialist agents worked on different "
        "dimensions of the same task in parallel. Produce a concise executive summary "
        "that captures the most important insights from all agents. Prioritise clarity "
        "and brevity — a busy decision-maker should be able to read this in 60 seconds.\n\n"
        f"Original task:\n{task}\n\n"
        f"Specialist outputs:\n{block}\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "final_answer": "concise executive summary in markdown (max 300 words)",\n'
        '  "key_themes": ["theme1", "theme2", "theme3"],\n'
        '  "reasoning": "what you prioritised and why"\n'
        "}"
    )
    raw = generate_response(prompt)
    data = _extract_json(raw)
    return {
        "mode": "summarise",
        "final_answer": data.get("final_answer", raw),
        "key_themes": data.get("key_themes", []),
        "reasoning": data.get("reasoning", ""),
        "winner": None,
    }


def _synthesise_vote(task: str, results: list[dict]) -> dict:
    """Pick the single best agent output, explaining why it wins."""
    block = _format_results_block(results)
    agent_names = [r["agent_name"] for r in results]
    prompt = (
        "You are a senior judge evaluating outputs from multiple specialist agents "
        "who each tackled a sub-task in parallel. Select the single most valuable "
        "output — the one that best addresses the original task — and explain why "
        "it outperforms the others.\n\n"
        f"Original task:\n{task}\n\n"
        f"Agent outputs:\n{block}\n\n"
        f"Agent names: {agent_names}\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "winner": "exact agent name from the list",\n'
        '  "final_answer": "the winning output (you may lightly edit for clarity)",\n'
        '  "key_themes": ["strength1", "strength2"],\n'
        '  "reasoning": "why this output wins over the others"\n'
        "}"
    )
    raw = generate_response(prompt)
    data = _extract_json(raw)
    return {
        "mode": "vote",
        "final_answer": data.get("final_answer", raw),
        "key_themes": data.get("key_themes", []),
        "reasoning": data.get("reasoning", ""),
        "winner": data.get("winner", ""),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def synthesise(task: str, results: list[dict], mode: str = "merge") -> dict:
    """Aggregate parallel agent results into a final answer.

    Parameters
    ----------
    task    : Original task that was fanned out.
    results : List of dicts from each specialist agent.
    mode    : "merge" | "summarise" | "vote"

    Returns
    -------
    {
        "mode"        : str            — aggregation strategy used
        "final_answer": str            — synthesised output
        "key_themes"  : list[str]      — top themes / strengths
        "reasoning"   : str            — synthesiser's rationale
        "winner"      : str | None     — winning agent (vote mode only)
    }
    """
    if not results:
        raise ValueError("Cannot synthesise zero results.")

    mode = mode.lower()
    if mode == "merge":
        return _synthesise_merge(task, results)
    if mode == "summarise":
        return _synthesise_summarise(task, results)
    if mode == "vote":
        return _synthesise_vote(task, results)

    raise ValueError(f"Unknown synthesis mode: {mode!r}. Choose merge | summarise | vote.")
