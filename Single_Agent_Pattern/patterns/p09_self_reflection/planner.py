"""Self-Reflection planner — creates an initial plan with tool selections.

Each step immediately selects a single approach AND the tool (if any) it
intends to use.  The reflector will later critique these choices before
any tool is actually invoked.
"""

import json
import re

from shared.llm import generate_response
from shared.tools import tool_descriptions_text


def _extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON found:\n{text[:400]}")


def create_plan(user_goal: str) -> list[dict]:
    """Generate a 3-5 step plan.  For each step the LLM picks one approach
    and decides whether a tool is needed.

    Returns a list of dicts:
        [{
            step_number   : int,
            goal          : str,
            approach      : str,
            tool_name     : str | null,
            tool_params   : dict,
            reasoning     : str,
        }, ...]
    """
    prompt = (
        f'Goal: "{user_goal}"\n\n'
        "You are planning how to accomplish the goal above. "
        "Generate a plan with 3-5 sequential steps.\n\n"
        "For EACH step decide:\n"
        "  1. A clear sub-goal.\n"
        "  2. The single best approach to achieve it.\n"
        "  3. Whether a tool should be used (pick from the list below or set null).\n"
        "  4. If a tool is chosen, the parameters to pass.\n"
        "  5. Brief reasoning for your choices.\n\n"
        "Available tools:\n"
        f"{tool_descriptions_text()}\n\n"
        "Respond with JSON only:\n"
        "```json\n"
        '{"steps":['
        '{"step_number":1,"goal":"...","approach":"...","tool_name":"...or null",'
        '"tool_params":{},"reasoning":"..."}'
        "]}\n"
        "```"
    )
    raw = generate_response(prompt)
    try:
        steps = _extract_json(raw).get("steps", [])
        return steps or [{"step_number": 1, "goal": "Execute goal",
                          "approach": "Direct", "tool_name": None,
                          "tool_params": {}, "reasoning": raw}]
    except Exception:
        return [{"step_number": 1, "goal": "Execute goal",
                 "approach": "Direct", "tool_name": None,
                 "tool_params": {}, "reasoning": raw}]
