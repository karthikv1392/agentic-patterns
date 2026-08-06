"""Multi-path executor — runs the chosen option for each step.

Identical in structure to p07's executor: decide on tool → (optionally)
execute tool → generate step output. Separated so learners see it as
the same execution component reused in a more complex pattern.
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
    raise ValueError(f"No JSON:\n{text[:400]}")


def execute_step(
    user_goal: str,
    step_number: int,
    step_goal: str,
    chosen_approach: str,
    chosen_description: str,
    accumulated_context: str,
) -> dict:
    """Execute one step using the chosen approach.

    Returns:
        tool_used   : tool name or None
        tool_output : raw tool result or None
        output      : final LLM-generated step output
    """
    context_block = (
        f"\n\nContext from completed steps:\n{accumulated_context}"
        if accumulated_context else ""
    )

    # 1. Tool decision
    decision_prompt = (
        f"Goal: \"{user_goal}\"\n"
        f"Step {step_number}: {step_goal}\n"
        f"Chosen approach: {chosen_approach} — {chosen_description}"
        f"{context_block}\n\n"
        "Available tools:\n"
        f"{tool_descriptions_text()}\n\n"
        "Does this step benefit from calling a tool? Respond with JSON only:\n"
        "```json\n"
        '{"needs_tool":true,"tool_name":"...","parameters":{...},"reasoning":"..."}\n'
        "```\nor\n"
        "```json\n"
        '{"needs_tool":false,"tool_name":null,"parameters":{},"reasoning":"..."}\n'
        "```"
    )
    raw_decision = generate_response(decision_prompt)

    tool_used = None
    tool_output = None
    try:
        d = _extract_json(raw_decision)
        if d.get("needs_tool") and d.get("tool_name") in TOOL_REGISTRY:
            tool_used   = d["tool_name"]
            tool_output = execute_tool(tool_used, d.get("parameters", {}))
    except Exception:
        pass

    # 2. Step execution
    tool_block = (
        f"\n\nTool used: {tool_used}\nTool output:\n```\n{tool_output}\n```"
        if tool_output else ""
    )
    exec_prompt = (
        f"Goal: \"{user_goal}\"\n"
        f"Step {step_number}: {step_goal}\n"
        f"Approach: {chosen_approach} — {chosen_description}"
        f"{context_block}"
        f"{tool_block}\n\n"
        "Produce a detailed, well-structured output for this step. "
        "Incorporate the tool result if provided. Use markdown."
    )
    output = generate_response(exec_prompt)

    return {"tool_used": tool_used, "tool_output": tool_output, "output": output}
