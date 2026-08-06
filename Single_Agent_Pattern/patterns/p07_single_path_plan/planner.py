"""Single-path planner — generates a linear ordered plan.

Separated from executor.py and agent.py so learners can see that
*planning* (deciding what to do) and *execution* (doing it) are
distinct responsibilities.
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
    """Ask the LLM to generate an ordered list of 4-6 steps.

    Returns a list of dicts: [{step_number, description}, ...]
    """
    prompt = (
        f"Goal: \"{user_goal}\"\n\n"
        "Generate a clear, linear plan with 4-6 ordered steps. "
        "Each step is one concrete action.\n\n"
        "Available tools steps may use:\n"
        f"{tool_descriptions_text()}\n\n"
        "Respond with JSON only:\n"
        "```json\n"
        '{"steps":[{"step_number":1,"description":"..."},...] }\n'
        "```"
    )
    raw = generate_response(prompt)
    try:
        return _extract_json(raw).get("steps", []) or [{"step_number": 1, "description": raw}]
    except Exception:
        return [{"step_number": 1, "description": raw}]
