"""Self-Reflection executor — runs each step of the (possibly revised) plan.

Executes the tool chosen during planning/reflection (if any), then asks
the LLM to produce the step's output incorporating the tool result.
"""

from shared.llm import generate_response
from shared.tools import TOOL_REGISTRY, execute_tool


def execute_step(
    user_goal: str,
    step: dict,
    accumulated_context: str,
) -> dict:
    """Execute one step from the reflected-and-approved plan.

    Args:
        user_goal           : The user's original goal.
        step                : A step dict from the (possibly revised) plan.
        accumulated_context : Outputs from all previously completed steps.

    Returns:
        tool_used   : tool name or None
        tool_output : raw tool result or None
        output      : final LLM-generated step output (markdown)
    """
    step_number  = step.get("step_number", "?")
    step_goal    = step.get("goal", "")
    approach     = step.get("approach", "")
    tool_name    = step.get("tool_name")
    tool_params  = step.get("tool_params") or {}

    context_block = (
        f"\n\nContext from completed steps:\n{accumulated_context}"
        if accumulated_context else ""
    )

    # Execute the tool selected during planning (already approved by reflection)
    tool_used   = None
    tool_output = None
    if tool_name and tool_name in TOOL_REGISTRY:
        tool_used   = tool_name
        tool_output = execute_tool(tool_name, tool_params)

    tool_block = (
        f"\n\nTool used: {tool_used}\nTool output:\n```\n{tool_output}\n```"
        if tool_output else ""
    )

    exec_prompt = (
        f'Goal: "{user_goal}"\n'
        f"Step {step_number}: {step_goal}\n"
        f"Approach: {approach}"
        f"{context_block}"
        f"{tool_block}\n\n"
        "Produce a detailed, well-structured output for this step. "
        "Incorporate the tool result if provided. Use markdown."
    )
    output = generate_response(exec_prompt)

    return {"tool_used": tool_used, "tool_output": tool_output, "output": output}
