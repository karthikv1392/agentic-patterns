"""Incremental Tool Agent — agent.

The agent queries the LLM *three times*, each round receiving the
original goal plus all previous round responses as context:

  Round 1 — Goal analysis: what is needed?
  Round 2 — Goal + R1 → Action plan + tool selection
  Round 3 — Goal + R1 + R2 → Exact tool parameters (JSON)
  Execution — Run the tool
  Synthesis — Combine all context + tool output → final answer

Contrast with p05_one_step_tool_agent where all three rounds collapse
into a single LLM call.
"""

import json
import re

from shared.llm import generate_response
from shared.tools import TOOL_REGISTRY, execute_tool, tool_descriptions_text


def _extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON found:\n{text[:400]}")


def run(user_goal: str) -> dict:
    """
    Args:
        user_goal: The user's goal or question.

    Returns:
        rounds          : list of {round, label, response} dicts
        selected_tool   : Tool chosen in Round 3
        tool_parameters : Parameters chosen in Round 3
        tool_output     : Raw tool result
        final_output    : Synthesised final answer
    """

    rounds = []

    # --- Round 1: goal analysis ---
    r1_prompt = (
        f"Goal: \"{user_goal}\"\n\n"
        "Analyse this goal thoroughly. Identify the core objective, implicit "
        "constraints, what information or capabilities are needed, and any "
        "ambiguities. Do NOT propose solutions yet."
    )
    r1 = generate_response(r1_prompt)
    rounds.append({"round": 1, "label": "Goal Analysis", "response": r1})

    # --- Round 2: action plan + tool selection ---
    r2_prompt = (
        f"Goal: \"{user_goal}\"\n\n"
        f"=== Round 1 Analysis ===\n{r1}\n===\n\n"
        "Now write a numbered action plan (3-5 steps) and select the single "
        "best tool from the list below. Explain why.\n\n"
        f"Available tools:\n{tool_descriptions_text()}\n\n"
        "Do NOT specify exact parameters yet."
    )
    r2 = generate_response(r2_prompt)
    rounds.append({"round": 2, "label": "Action Plan & Tool Selection", "response": r2})

    # --- Round 3: exact tool parameters ---
    r3_prompt = (
        f"Goal: \"{user_goal}\"\n\n"
        f"=== Round 1 ===\n{r1}\n===\n\n"
        f"=== Round 2 ===\n{r2}\n===\n\n"
        "Finalise the tool call. Respond with JSON only:\n"
        "```json\n"
        '{"selected_tool":"...","parameters":{...}}\n'
        "```"
    )
    r3 = generate_response(r3_prompt)
    rounds.append({"round": 3, "label": "Precise Tool Parameters", "response": r3})

    # --- Parse and execute ---
    try:
        spec = _extract_json(r3)
        selected_tool   = spec.get("selected_tool", "none")
        tool_parameters = spec.get("parameters", {})
    except Exception:
        selected_tool, tool_parameters = "none", {}

    tool_output = (
        execute_tool(selected_tool, tool_parameters)
        if selected_tool in TOOL_REGISTRY
        else f"Tool '{selected_tool}' not found."
    )

    # --- Synthesis ---
    final_output = generate_response(
        f"Goal: \"{user_goal}\"\n\n"
        f"Round 1:\n{r1}\n\nRound 2:\n{r2}\n\n"
        f"Tool: {selected_tool} | Params: {json.dumps(tool_parameters)}\n"
        f"Tool output:\n```\n{tool_output}\n```\n\n"
        "Produce a comprehensive, well-structured final answer. Use markdown."
    )

    return {
        "rounds": rounds,
        "selected_tool": selected_tool,
        "tool_parameters": tool_parameters,
        "tool_output": tool_output,
        "final_output": final_output,
    }
