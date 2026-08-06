"""Passive Goal Creator — single-agent pattern demo.

The user provides a plain text prompt. The agent interprets the goal and
executes it step-by-step using the LLM without any additional context
enrichment.
"""

from utils import generate_response


def run_passive(user_prompt: str) -> dict:
    """Run the passive goal creator pipeline.

    Steps:
        1. Analyze the goal to identify sub-tasks.
        2. Execute each sub-task via the LLM.
        3. Combine results into a final output.

    Returns a dict with keys: goal_analysis, final_output
    """

    # Step 1 — Analyze the goal
    analysis_prompt = (
        "You are a planning assistant. A user has the following goal:\n\n"
        f'"{user_prompt}"\n\n'
        "Break this goal down into 3-5 concrete sub-tasks that, when completed "
        "together, fully address the goal. Return ONLY a numbered list of sub-tasks."
    )
    goal_analysis = generate_response(analysis_prompt)

    # Step 2 & 3 — Execute the full goal using the sub-task plan as guidance
    execution_prompt = (
        "You are an expert assistant. A user asked:\n\n"
        f'"{user_prompt}"\n\n'
        "You have already planned the following sub-tasks:\n"
        f"{goal_analysis}\n\n"
        "Now execute ALL of these sub-tasks and produce a comprehensive, "
        "well-structured final answer that addresses the original goal. "
        "Use markdown formatting for readability."
    )
    final_output = generate_response(execution_prompt)

    return {
        "goal_analysis": goal_analysis,
        "final_output": final_output,
    }


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    default_prompt = "Create a travel itinerary for 3 days in Tokyo"
    print(f"Running Passive Goal Creator with prompt: {default_prompt!r}\n")

    result = run_passive(default_prompt)

    print("=" * 60)
    print("GOAL ANALYSIS")
    print("=" * 60)
    print(result["goal_analysis"])
    print()
    print("=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(result["final_output"])
