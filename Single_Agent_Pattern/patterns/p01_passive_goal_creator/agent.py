"""Passive Goal Creator — agent.

The user provides a plain-text goal. The agent:
  1. Analyses the goal and breaks it into 3-5 sub-tasks  (LLM call 1)
  2. Executes all sub-tasks and produces the final answer (LLM call 2)

No external context or tools are used — only the LLM.
"""

from shared.llm import generate_response


def run(user_prompt: str) -> dict:
    """
    Args:
        user_prompt: The user's goal or task.

    Returns:
        goal_analysis : LLM-generated sub-task breakdown
        final_output  : Comprehensive final answer
    """

    # --- Step 1: break goal into sub-tasks ---
    analysis_prompt = (
        "You are a planning assistant. A user has the following goal:\n\n"
        f'"{user_prompt}"\n\n'
        "Break this goal down into 3-5 concrete sub-tasks that, when completed "
        "together, fully address the goal. Return ONLY a numbered list of sub-tasks."
    )
    goal_analysis = generate_response(analysis_prompt)

    # --- Step 2: execute all sub-tasks and synthesise ---
    execution_prompt = (
        "You are an expert assistant. A user asked:\n\n"
        f'"{user_prompt}"\n\n'
        "You have already planned the following sub-tasks:\n"
        f"{goal_analysis}\n\n"
        "Now execute ALL of these sub-tasks and produce a comprehensive, "
        "well-structured final answer. Use markdown formatting."
    )
    final_output = generate_response(execution_prompt)

    return {"goal_analysis": goal_analysis, "final_output": final_output}
