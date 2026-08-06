"""Single Path Plan Generator — agent.

Orchestrates planner.py and executor.py:
  1. planner  → creates a linear ordered plan
  2. executor → runs each step (with optional tool use)
  3. LLM      → synthesises all step outputs into a final answer
"""

from shared.llm import generate_response
from patterns.p07_single_path_plan.planner import create_plan
from patterns.p07_single_path_plan.executor import execute_step


def run(user_goal: str) -> dict:
    """
    Args:
        user_goal: The user's goal or task.

    Returns:
        plan_steps   : [{step_number, description}, ...]
        step_outputs : [{step_number, description, tool_used, tool_output, output}, ...]
        final_output : Synthesised final answer
    """

    # Step 1: plan
    plan_steps = create_plan(user_goal)

    # Step 2: execute each step sequentially
    step_outputs = []
    accumulated_context = ""

    for step in plan_steps:
        num  = step.get("step_number", len(step_outputs) + 1)
        desc = step.get("description", "")

        result = execute_step(user_goal, num, desc, accumulated_context)

        step_outputs.append({
            "step_number": num,
            "description": desc,
            "tool_used":   result["tool_used"],
            "tool_output": result["tool_output"],
            "output":      result["output"],
        })
        accumulated_context += (
            f"\nStep {num} ({desc})"
            + (f" [tool: {result['tool_used']}]" if result["tool_used"] else "")
            + f":\n{result['output']}\n"
        )

    # Step 3: synthesise
    steps_summary = "\n\n".join(
        f"**Step {s['step_number']}: {s['description']}**\n{s['output']}"
        for s in step_outputs
    )
    final_output = generate_response(
        f"Goal: \"{user_goal}\"\n\nSteps executed:\n\n{steps_summary}\n\n"
        "Synthesise all of the above into a single, coherent, comprehensive "
        "final answer. Integrate — do not repeat verbatim. Use markdown."
    )

    return {
        "plan_steps": plan_steps,
        "step_outputs": step_outputs,
        "final_output": final_output,
    }
