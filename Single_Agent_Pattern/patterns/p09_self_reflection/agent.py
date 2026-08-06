"""Self-Reflection Pattern — agent.

Orchestrates planner → reflector → executor:

  1. planner   → creates an initial plan (steps with approach + tool selection)
  2. reflector → critiques the plan internally, identifies issues, revises if needed
  3. executor  → executes the REFLECTED (approved/revised) plan step by step
  4. LLM       → synthesises all step outputs into a final answer

The reflection step is the key differentiator: the agent checks its own
reasoning before taking any real action.
"""

from shared.llm import generate_response
from patterns.p09_self_reflection.planner   import create_plan
from patterns.p09_self_reflection.reflector import reflect
from patterns.p09_self_reflection.executor  import execute_step


def run(user_goal: str) -> dict:
    """
    Args:
        user_goal: The user's goal or task.

    Returns:
        initial_plan    : [{step_number, goal, approach, tool_name, tool_params, reasoning}, ...]
        reflection      : {is_sound, issues, reflection_text, changes_made, revised_steps}
        final_plan      : the plan actually executed (initial or revised)
        step_outputs    : [{step_number, goal, approach, tool_used, tool_output, output}, ...]
        final_output    : synthesised markdown answer
    """

    # ── 1. Plan ───────────────────────────────────────────────────────────────
    initial_plan = create_plan(user_goal)

    # ── 2. Reflect ────────────────────────────────────────────────────────────
    reflection = reflect(user_goal, initial_plan)
    final_plan = reflection["revised_steps"]

    # ── 3. Execute ────────────────────────────────────────────────────────────
    step_outputs        = []
    accumulated_context = ""

    for step in final_plan:
        result = execute_step(user_goal, step, accumulated_context)

        step_outputs.append({
            "step_number": step.get("step_number", len(step_outputs) + 1),
            "goal":        step.get("goal", ""),
            "approach":    step.get("approach", ""),
            "tool_used":   result["tool_used"],
            "tool_output": result["tool_output"],
            "output":      result["output"],
        })

        num  = step.get("step_number", len(step_outputs))
        goal = step.get("goal", "")
        acc_tool = f" [tool: {result['tool_used']}]" if result["tool_used"] else ""
        accumulated_context += (
            f"\nStep {num} ({goal}) [approach: {step.get('approach', '')}]"
            f"{acc_tool}:\n{result['output']}\n"
        )

    # ── 4. Synthesise ─────────────────────────────────────────────────────────
    steps_summary = "\n\n".join(
        f"**Step {s['step_number']}: {s['goal']}** *(approach: {s['approach']})*\n{s['output']}"
        for s in step_outputs
    )
    final_output = generate_response(
        f'Goal: "{user_goal}"\n\n'
        "A self-reflecting agent planned its approach, critiqued its own plan, "
        "revised where needed, and then executed each step. Results:\n\n"
        f"{steps_summary}\n\n"
        "Synthesise all of the above into a single, coherent, comprehensive "
        "final answer. Use markdown."
    )

    return {
        "initial_plan": initial_plan,
        "reflection":   reflection,
        "final_plan":   final_plan,
        "step_outputs": step_outputs,
        "final_output": final_output,
    }
