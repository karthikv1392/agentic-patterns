"""Self-Reflection reflector — the agent critiques its own plan.

The LLM is shown the initial plan it just created and asked to:
  • Identify any flaws in approach or tool selection.
  • Confirm whether each step's tool choice is appropriate.
  • Produce a revised plan if changes are needed.

This makes the "reflection" step visible and explicit rather than hiding
it inside a single monolithic prompt.
"""

import json
import re

from shared.llm import generate_response
from shared.tools import tool_descriptions_text, TOOL_REGISTRY


def _extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON found:\n{text[:400]}")


def _plan_text(steps: list[dict]) -> str:
    lines = []
    for s in steps:
        tool_info = (
            f"Tool: {s['tool_name']} | Params: {json.dumps(s.get('tool_params', {}))}"
            if s.get("tool_name") else "Tool: none"
        )
        lines.append(
            f"Step {s['step_number']}: {s['goal']}\n"
            f"  Approach : {s['approach']}\n"
            f"  {tool_info}\n"
            f"  Reasoning: {s.get('reasoning', '')}"
        )
    return "\n\n".join(lines)


def reflect(user_goal: str, initial_steps: list[dict]) -> dict:
    """Reflect on the initial plan and optionally revise it.

    Returns:
        is_sound        : bool   — True if no significant issues found
        issues          : list[str]  — issues identified (empty if sound)
        reflection_text : str    — full free-text reflection
        revised_steps   : list[dict] — revised plan (same as initial if no changes)
        changes_made    : bool   — True if any step was revised
    """
    plan_text = _plan_text(initial_steps)
    available_tools = ", ".join(TOOL_REGISTRY.keys())

    prompt = (
        f'Original goal: "{user_goal}"\n\n'
        "You previously created the following plan:\n\n"
        f"{plan_text}\n\n"
        "Now reflect critically on this plan BEFORE executing it. Check:\n"
        "  1. Is every step's approach the best way to achieve its sub-goal?\n"
        "  2. Is each tool selection appropriate (or should a different tool / no tool be used)?\n"
        "  3. Are tool parameters correct and complete?\n"
        "  4. Are the steps in the right order? Are any steps missing or redundant?\n"
        "  5. Does the overall path actually achieve the original goal?\n\n"
        f"Available tools: {available_tools}\n\n"
        "After reflecting, decide if the plan needs revision.\n\n"
        "Respond with JSON only:\n"
        "```json\n"
        "{\n"
        '  "is_sound": true,\n'
        '  "issues": ["issue 1 if any", "issue 2 if any"],\n'
        '  "reflection_text": "Your detailed reasoning about what is good or bad about the plan...",\n'
        '  "changes_made": false,\n'
        '  "revised_steps": [\n'
        '    {"step_number":1,"goal":"...","approach":"...","tool_name":"...or null","tool_params":{},"reasoning":"..."}\n'
        "  ]\n"
        "}\n"
        "```\n"
        "If the plan is already sound, set is_sound=true, issues=[], changes_made=false, "
        "and copy the original steps unchanged into revised_steps."
    )
    raw = generate_response(prompt)
    try:
        data = _extract_json(raw)
        revised = data.get("revised_steps") or initial_steps
        # Ensure revised_steps is a non-empty list
        if not isinstance(revised, list) or not revised:
            revised = initial_steps
        return {
            "is_sound":        bool(data.get("is_sound", True)),
            "issues":          data.get("issues", []),
            "reflection_text": data.get("reflection_text", raw),
            "changes_made":    bool(data.get("changes_made", False)),
            "revised_steps":   revised,
        }
    except Exception:
        return {
            "is_sound":        True,
            "issues":          [],
            "reflection_text": raw,
            "changes_made":    False,
            "revised_steps":   initial_steps,
        }
