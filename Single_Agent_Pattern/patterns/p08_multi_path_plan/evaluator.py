"""Multi-path evaluator — selects the best option for each step.

Separated so learners see that *evaluation* (choosing between paths)
is a distinct cognitive step from planning or execution.
"""

import json
import re

from shared.llm import generate_response


def _extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON:\n{text[:400]}")


def evaluate_options(
    user_goal: str,
    step_number: int,
    step_goal: str,
    options: list[dict],
    accumulated_context: str,
) -> dict:
    """Pick the best option for a given step.

    Returns:
        chosen_option_id : "A", "B", or "C"
        approach         : short name of the chosen approach
        rationale        : why this option was selected
    """
    options_text = "\n".join(
        f"  Option {o['id']}: {o['approach']} — {o['description']}" for o in options
    )
    context_block = (
        f"\n\nContext from completed steps:\n{accumulated_context}"
        if accumulated_context else ""
    )
    prompt = (
        f"Goal: \"{user_goal}\"\n"
        f"Step {step_number}: {step_goal}"
        f"{context_block}\n\n"
        f"Options:\n{options_text}\n\n"
        "Evaluate each option for effectiveness, feasibility, and fit with "
        "prior context. Select the single best option.\n\n"
        "Respond with JSON only:\n"
        "```json\n"
        '{"chosen_option_id":"...","chosen_approach":"...","rationale":"..."}\n'
        "```"
    )
    raw = generate_response(prompt)
    try:
        ev = _extract_json(raw)
        return {
            "chosen_option_id": ev.get("chosen_option_id", options[0]["id"] if options else "A"),
            "approach":         ev.get("chosen_approach", ""),
            "rationale":        ev.get("rationale", ""),
        }
    except Exception:
        return {
            "chosen_option_id": options[0]["id"] if options else "A",
            "approach":         options[0].get("approach", "") if options else "",
            "rationale":        raw,
        }
