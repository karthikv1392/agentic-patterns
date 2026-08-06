"""Prompt Optimizer — agent.

The user provides a rough prompt. The agent:
  1. Calls the optimiser (optimizer.py) to rewrite it   (LLM call 1)
  2. Sends the optimised prompt to the LLM for the task (LLM call 2)

The key insight: a well-engineered prompt consistently yields
higher-quality outputs than a vague one.
"""

from shared.llm import generate_response
from patterns.p03_prompt_optimizer.optimizer import optimize


def run(user_prompt: str) -> dict:
    """
    Args:
        user_prompt: The user's raw, possibly vague prompt.

    Returns:
        original_prompt  : The input as provided
        optimized_prompt : The LLM-rewritten version
        final_output     : Response to the optimised prompt
    """

    # Step 1: optimise
    optimized_prompt = optimize(user_prompt)

    # Step 2: execute the optimised prompt
    final_output = generate_response(optimized_prompt)

    return {
        "original_prompt": user_prompt,
        "optimized_prompt": optimized_prompt,
        "final_output": final_output,
    }
