"""Single-path executor — runs each plan step with optional tool use.

For every step the executor:
  1. Asks the LLM whether a tool is needed (tool decision)
  2. Executes the tool if required
  3. Calls the LLM to produce the step output using the tool result
     and all prior step context

Separated from planner.py so learners can clearly see the
decide-act-observe loop happening inside each step.
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
    step_description: str,
    accumulated_context: str,
) -> dict:
    """Execute one plan step.

    Returns a dict:
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
        f"Step {step_number}: {step_description}"
        f"{context_block}\n\n"
        "Available tools:\n"
        f"{tool_descriptions_text()}\n\n"
        "Does this step benefit from calling a tool? "
        "Respond with JSON only:\n"
        "```json\n"
        '{"needs_tool":true,"tool_name":"...","parameters":{...},"reasoning":"..."}\n'
        "```\n"
        "or\n"
        "```json\n"
        '{"needs_tool":false,"tool_name":null,"parameters":{},\"reasoning\":\"...\"}\n'
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
        f"Step {step_number}: {step_description}"
        f"{context_block}"
        f"{tool_block}\n\n"
        "Produce a detailed, well-structured output for this step. "
        "Incorporate the tool result if provided. Use markdown."
    )
    output = generate_response(exec_prompt)

    return {"tool_used": tool_used, "tool_output": tool_output, "output": output}
