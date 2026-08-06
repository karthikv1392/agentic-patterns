"""Multi-path planner — generates a plan where each step has 2-3 options.

Separated so learners see that planning here means producing a *branching*
structure, not just a flat list.
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
    raise ValueError(f"No JSON:\n{text[:400]}")


def create_plan(user_goal: str) -> list[dict]:
    """Generate 3-5 steps, each with 2-3 alternative approaches.

    Returns a list of dicts:
        [{step_number, goal, options:[{id, approach, description}]}, ...]
    """
    prompt = (
        f"Goal: \"{user_goal}\"\n\n"
        "Generate a plan with 3-5 steps. For each step provide 2-3 distinct "
        "alternative approaches (different strategies, not just wording variants).\n\n"
        "Available tools steps may use:\n"
        f"{tool_descriptions_text()}\n\n"
        "Respond with JSON only:\n"
        "```json\n"
        '{"steps":[{"step_number":1,"goal":"...","options":['
        '{"id":"A","approach":"...","description":"..."},'
        '{"id":"B","approach":"...","description":"..."}]}]}\n'
        "```"
    )
    raw = generate_response(prompt)
    try:
        steps = _extract_json(raw).get("steps", [])
        return steps or [{"step_number": 1, "goal": "Execute goal", "options": [
            {"id": "A", "approach": "Direct", "description": raw}
        ]}]
    except Exception:
        return [{"step_number": 1, "goal": "Execute goal", "options": [
            {"id": "A", "approach": "Direct", "description": raw}
        ]}]
