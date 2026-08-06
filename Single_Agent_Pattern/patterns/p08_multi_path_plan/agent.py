"""Multi-Path Plan Generator — agent.

Orchestrates planner.py, evaluator.py, and executor.py:
  1. planner   → creates a branching plan (steps with options)
  2. evaluator → picks the best option per step
  3. executor  → runs the chosen option (with optional tool use)
  4. LLM       → synthesises all step outputs → final answer
"""

from shared.llm import generate_response
from patterns.p08_multi_path_plan.planner import create_plan
from patterns.p08_multi_path_plan.evaluator import evaluate_options
from patterns.p08_multi_path_plan.executor import execute_step


def run(user_goal: str) -> dict:
    """
    Args:
        user_goal: The user's goal or task.

    Returns:
        plan_steps   : [{step_number, goal, options:[...]}, ...]
        evaluations  : [{step_number, chosen_option_id, approach, rationale}, ...]
        step_outputs : [{step_number, goal, chosen_approach, tool_used,
                         tool_output, output}, ...]
        final_output : Synthesised final answer
    """

    # Step 1: plan
    plan_steps = create_plan(user_goal)

    # Steps 2-4: evaluate + execute each step
    evaluations  = []
    step_outputs = []
    accumulated_context = ""

    for step in plan_steps:
        num     = step.get("step_number", len(step_outputs) + 1)
        goal    = step.get("goal", "")
        options = step.get("options", [])

        # Evaluate options
        ev = evaluate_options(user_goal, num, goal, options, accumulated_context)
        evaluations.append({"step_number": num, **ev})

        chosen_id   = ev["chosen_option_id"]
        chosen_desc = next(
            (o["description"] for o in options if o["id"] == chosen_id),
            ev["approach"],
        )

        # Execute chosen option
        result = execute_step(
            user_goal, num, goal, ev["approach"], chosen_desc, accumulated_context
        )

        step_outputs.append({
            "step_number":    num,
            "goal":           goal,
            "chosen_approach": ev["approach"],
            "tool_used":      result["tool_used"],
            "tool_output":    result["tool_output"],
            "output":         result["output"],
        })
        accumulated_context += (
            f"\nStep {num} ({goal}) [approach: {ev['approach']}]"
            + (f" [tool: {result['tool_used']}]" if result["tool_used"] else "")
            + f":\n{result['output']}\n"
        )

    # Synthesise
    steps_summary = "\n\n".join(
        f"**Step {s['step_number']}: {s['goal']}** *(approach: {s['chosen_approach']})*\n{s['output']}"
        for s in step_outputs
    )
    final_output = generate_response(
        f"Goal: \"{user_goal}\"\n\n"
        "A multi-path agent evaluated options and executed the best approach "
        "at each step. Results:\n\n"
        f"{steps_summary}\n\n"
        "Synthesise all of the above into a single, coherent, comprehensive "
        "final answer. Use markdown."
    )

    return {
        "plan_steps":   plan_steps,
        "evaluations":  evaluations,
        "step_outputs": step_outputs,
        "final_output": final_output,
    }
