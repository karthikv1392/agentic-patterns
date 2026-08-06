"""One-Step Tool Agent — agent.

The user provides a goal. In a *single* LLM call the agent:
  1. Writes a step-by-step plan
  2. Selects the best tool + parameters  (all returned as JSON)

The tool is then executed and the result is fed back to the LLM
for a final grounded answer.

Contrast with p06_incremental_tool_agent where the same work is
spread across three separate LLM calls.
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
        plan            : Natural-language plan from the LLM
        reasoning       : Why the chosen tool was selected
        selected_tool   : Tool name
        tool_parameters : Parameters passed to the tool
        tool_output     : Raw tool result
        final_output    : Synthesised final answer
    """

    # --- Single LLM call: plan + tool selection ---
    planning_prompt = (
        "You are an expert AI agent. The user's goal:\n\n"
        f'"{user_goal}"\n\n'
        "Available tools:\n"
        f"{tool_descriptions_text()}\n\n"
        "In one response:\n"
        "1. Write a concise step-by-step plan.\n"
        "2. Pick the single most useful tool.\n"
        "3. Specify exact parameters for that tool.\n\n"
        "Respond with JSON only:\n"
        "```json\n"
        '{"plan":"...","reasoning":"...","selected_tool":"...","parameters":{...}}\n'
        "```"
    )
    raw = generate_response(planning_prompt)

    try:
        parsed = _extract_json(raw)
    except Exception:
        parsed = {"plan": raw, "reasoning": "", "selected_tool": "none", "parameters": {}}

    plan            = parsed.get("plan", "")
    reasoning       = parsed.get("reasoning", "")
    selected_tool   = parsed.get("selected_tool", "none")
    tool_parameters = parsed.get("parameters", {})

    # --- Execute tool ---
    tool_output = (
        execute_tool(selected_tool, tool_parameters)
        if selected_tool in TOOL_REGISTRY
        else f"Tool '{selected_tool}' not found."
    )

    # --- Synthesise final answer ---
    final_output = generate_response(
        f"User goal: \"{user_goal}\"\n\n"
        f"Plan:\n{plan}\n\n"
        f"Tool used: {selected_tool}\nTool output:\n```\n{tool_output}\n```\n\n"
        "Produce a comprehensive, well-structured final answer. Use markdown."
    )

    return {
        "plan": plan,
        "reasoning": reasoning,
        "selected_tool": selected_tool,
        "tool_parameters": tool_parameters,
        "tool_output": tool_output,
        "final_output": final_output,
    }
