"""Single Path Plan Generator — single-agent pattern demo.

The user provides a goal. The agent generates a linear, sequential plan
(an ordered list of steps). Each step is executed one at a time:

  1. The agent first decides whether the step requires a tool call.
  2. If a tool is needed, it is invoked and the result is injected as context.
  3. The LLM then produces the step output (using the tool result if available).

All prior step outputs are accumulated and passed forward as context into
each subsequent step, and finally synthesised into a coherent final answer.

Flow:
    User Goal
        → [LLM] generates ordered plan  (JSON)
        → for each step:
              [LLM] decides: tool needed? → (optional) tool execution
              [LLM] produces step output using tool result + prior context
        → [LLM] synthesises all step outputs → final answer
"""

import json
import re

from tools import TOOL_REGISTRY, execute_tool, tool_descriptions_text
from utils import generate_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict | list:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON found in LLM response:\n{text[:400]}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_single_path_plan_generator(user_goal: str) -> dict:
    """Run the single-path plan-generator pipeline.

    Steps:
        1. LLM generates a linear JSON plan of 4–6 ordered steps.
        2. For each step:
               a. LLM decides whether a tool is needed (returns JSON).
               b. Tool is executed if required.
               c. LLM produces the step output, grounded in tool result
                  and all prior step context.
        3. LLM synthesises all step outputs into a final answer.

    Returns a dict with keys:
        plan_steps    — list of {step_number, description}
        step_outputs  — list of {step_number, description, tool_used,
                                  tool_output, output}
        final_output  — synthesised final answer
    """

    # ------------------------------------------------------------------
    # Step 1 — Generate linear plan
    # ------------------------------------------------------------------
    plan_prompt = (
        "You are an expert planning agent. A user wants to achieve:\n\n"
        f'"{user_goal}"\n\n'
        "Generate a clear, linear, step-by-step plan with 4–6 ordered steps. "
        "Each step must be a single, concrete action.\n\n"
        "You have access to these tools that steps may later use:\n"
        f"{tool_descriptions_text()}\n\n"
        "Respond with a JSON object and nothing else:\n"
        "```json\n"
        "{\n"
        '  "steps": [\n'
        '    {"step_number": 1, "description": "<concrete action for this step>"},\n'
        '    {"step_number": 2, "description": "<concrete action for this step>"},\n'
        "    ...\n"
        "  ]\n"
        "}\n"
        "```"
    )
    raw_plan = generate_response(plan_prompt)

    try:
        plan_steps = _extract_json(raw_plan).get("steps", [])
        if not plan_steps:
            raise ValueError("empty")
    except Exception:
        plan_steps = [{"step_number": 1, "description": raw_plan}]

    # ------------------------------------------------------------------
    # Step 2 — Execute each step (with optional tool use)
    # ------------------------------------------------------------------
    step_outputs: list[dict] = []
    accumulated_context = ""

    for step in plan_steps:
        step_num = step.get("step_number", len(step_outputs) + 1)
        step_desc = step.get("description", "")
        context_block = (
            f"\n\nContext from completed steps:\n{accumulated_context}"
            if accumulated_context else ""
        )

        # -- 2a. Tool decision --
        tool_decision_prompt = (
            "You are an expert agent deciding whether to use a tool for a step.\n\n"
            f"Overall goal: \"{user_goal}\"\n"
            f"Current step ({step_num}): {step_desc}"
            f"{context_block}\n\n"
            "Available tools:\n"
            f"{tool_descriptions_text()}\n\n"
            "Decide: does this step benefit from calling one of the above tools? "
            "If yes, specify which tool and the exact parameters. "
            "If no tool is needed, set needs_tool to false.\n\n"
            "Respond with a JSON object and nothing else:\n"
            "```json\n"
            "{\n"
            '  "needs_tool": true or false,\n'
            '  "tool_name": "<tool name or null>",\n'
            '  "parameters": {<parameters or {}>},\n'
            '  "reasoning": "<why this tool helps, or why none is needed>"\n'
            "}\n"
            "```"
        )
        raw_decision = generate_response(tool_decision_prompt)

        tool_used = None
        tool_output = None
        try:
            decision = _extract_json(raw_decision)
            if decision.get("needs_tool") and decision.get("tool_name") in TOOL_REGISTRY:
                tool_used = decision["tool_name"]
                tool_output = execute_tool(tool_used, decision.get("parameters", {}))
        except Exception:
            pass  # proceed without tool

        # -- 2b. Step execution (with tool result if available) --
        tool_block = (
            f"\n\nTool used: {tool_used}\nTool output:\n```\n{tool_output}\n```"
            if tool_output else ""
        )
        exec_prompt = (
            "You are an expert assistant executing one step in a plan.\n\n"
            f"Overall goal: \"{user_goal}\"\n"
            f"Step {step_num}: {step_desc}"
            f"{context_block}"
            f"{tool_block}\n\n"
            "Produce a detailed, well-structured output for this step. "
            "If a tool result is provided, incorporate it directly. "
            "Use markdown formatting."
        )
        output = generate_response(exec_prompt)

        step_outputs.append({
            "step_number": step_num,
            "description": step_desc,
            "tool_used": tool_used,
            "tool_output": tool_output,
            "output": output,
        })
        accumulated_context += (
            f"\nStep {step_num} ({step_desc})"
            + (f" [tool: {tool_used}]" if tool_used else "")
            + f":\n{output}\n"
        )

    # ------------------------------------------------------------------
    # Step 3 — Synthesise final answer
    # ------------------------------------------------------------------
    steps_summary = "\n\n".join(
        f"**Step {s['step_number']}: {s['description']}**\n{s['output']}"
        for s in step_outputs
    )
    synthesis_prompt = (
        "You are an expert assistant. A user had the following goal:\n\n"
        f'"{user_goal}"\n\n'
        "The following steps were executed to achieve it:\n\n"
        f"{steps_summary}\n\n"
        "Synthesise all of the above into a single, coherent, comprehensive "
        "final answer. Integrate and summarise — do not repeat content verbatim. "
        "Use markdown formatting."
    )
    final_output = generate_response(synthesis_prompt)

    return {
        "plan_steps": plan_steps,
        "step_outputs": step_outputs,
        "final_output": final_output,
    }


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    default_goal = "Create a study plan for learning machine learning in 3 months"
    print(f"Running Single Path Plan Generator:\n  {default_goal!r}\n")

    result = run_single_path_plan_generator(default_goal)

    print("=" * 60)
    print("PLAN")
    print("=" * 60)
    for step in result["plan_steps"]:
        print(f"  Step {step['step_number']}: {step['description']}")

    print()
    for s in result["step_outputs"]:
        print("=" * 60)
        print(f"STEP {s['step_number']} — {s['description']}")
        if s["tool_used"]:
            print(f"  Tool: {s['tool_used']}")
            print(f"  Tool output: {s['tool_output']}")
        print("=" * 60)
        print(s["output"])
        print()

    print("=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(result["final_output"])
