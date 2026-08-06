"""One-Step Tool Agent — single-agent pattern demo.

Given a user goal, a single LLM call produces a structured plan AND selects
the tool + parameters required to accomplish it. The tool is then executed
and the result is fed back to the LLM for a final, grounded response.

Flow:
    User Goal
        → [LLM — single call]  produces plan + tool selection (JSON)
        → [Tool Executor]       runs the chosen tool
        → [LLM — synthesis]    combines goal + plan + tool output → final answer
"""

import json
import re

from tools import TOOL_REGISTRY, execute_tool, tool_descriptions_text
from utils import generate_response


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of an LLM response."""
    # 1. Try a fenced code block  ```json … ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())

    # 2. Try a bare { … } span
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"No JSON object found in LLM response:\n{text[:400]}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_one_step_tool_agent(user_goal: str) -> dict:
    """Run the one-step tool-agent pipeline.

    Steps:
        1. Single LLM call: analyse the goal, produce a plan, and select
           the best tool + parameters (returned as JSON).
        2. Execute the selected tool.
        3. LLM synthesis: produce the final answer using the goal, plan,
           and tool output.

    Returns a dict with keys:
        plan            — natural-language plan produced by the LLM
        reasoning       — LLM's justification for tool selection
        selected_tool   — name of the chosen tool
        tool_parameters — dict of parameters passed to the tool
        tool_output     — raw string output from the tool
        final_output    — final synthesised LLM response
    """

    # ------------------------------------------------------------------
    # Step 1 — Single LLM call: plan + tool selection
    # ------------------------------------------------------------------
    planning_prompt = (
        "You are an expert AI agent. A user has given you the following goal:\n\n"
        f'"{user_goal}"\n\n'
        "You have access to the following tools:\n\n"
        f"{tool_descriptions_text()}\n\n"
        "Your task:\n"
        "1. Write a concise step-by-step plan to accomplish the goal.\n"
        "2. Identify the single most useful tool from the list above that "
        "will help accomplish the goal.\n"
        "3. Specify the exact parameters to pass to that tool.\n\n"
        "Respond with a single JSON object and nothing else:\n"
        "```json\n"
        "{\n"
        '  "plan": "<numbered step-by-step plan as a single string>",\n'
        '  "reasoning": "<why you chose this tool>",\n'
        '  "selected_tool": "<exact tool name from the list>",\n'
        '  "parameters": {<tool parameters as key-value pairs>}\n'
        "}\n"
        "```"
    )
    raw_planning = generate_response(planning_prompt)

    try:
        planning_result = _extract_json(raw_planning)
    except (ValueError, json.JSONDecodeError) as exc:
        # Graceful fallback — surface the raw LLM text for debugging
        planning_result = {
            "plan": raw_planning,
            "reasoning": "Could not parse structured JSON from LLM response.",
            "selected_tool": "none",
            "parameters": {},
        }

    plan = planning_result.get("plan", "")
    reasoning = planning_result.get("reasoning", "")
    selected_tool = planning_result.get("selected_tool", "none")
    tool_parameters = planning_result.get("parameters", {})

    # ------------------------------------------------------------------
    # Step 2 — Execute the selected tool
    # ------------------------------------------------------------------
    if selected_tool in TOOL_REGISTRY:
        tool_output = execute_tool(selected_tool, tool_parameters)
    else:
        tool_output = f"Tool '{selected_tool}' not found; skipping execution."

    # ------------------------------------------------------------------
    # Step 3 — Final synthesis
    # ------------------------------------------------------------------
    synthesis_prompt = (
        "You are an expert assistant. A user asked:\n\n"
        f'"{user_goal}"\n\n'
        "You created the following plan:\n"
        f"{plan}\n\n"
        f"You then ran the tool **{selected_tool}** and received this output:\n"
        f"```\n{tool_output}\n```\n\n"
        "Using the plan and the tool output, produce a comprehensive, "
        "well-structured final answer that fully addresses the user's goal. "
        "Incorporate the tool result naturally. Use markdown formatting."
    )
    final_output = generate_response(synthesis_prompt)

    return {
        "plan": plan,
        "reasoning": reasoning,
        "selected_tool": selected_tool,
        "tool_parameters": tool_parameters,
        "tool_output": tool_output,
        "final_output": final_output,
    }


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    default_goal = "What is 18% tip on a dinner bill of $84.50, and what would each person pay if splitting 4 ways?"
    print(f"Running One-Step Tool Agent with goal:\n  {default_goal!r}\n")

    result = run_one_step_tool_agent(default_goal)

    print("=" * 60)
    print("PLAN")
    print("=" * 60)
    print(result["plan"])
    print()
    print("=" * 60)
    print(f"SELECTED TOOL: {result['selected_tool']}")
    print(f"REASONING: {result['reasoning']}")
    print(f"PARAMETERS: {result['tool_parameters']}")
    print("=" * 60)
    print()
    print("=" * 60)
    print("TOOL OUTPUT")
    print("=" * 60)
    print(result["tool_output"])
    print()
    print("=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(result["final_output"])
