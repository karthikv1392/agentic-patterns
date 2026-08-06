"""Prompt Optimizer — single-agent pattern demo.

The user provides a plain text prompt. Before passing it to the LLM for the
actual task, a first LLM call rewrites and optimises the prompt to be clearer,
more specific, and more likely to produce a high-quality response. The
optimised prompt is then used for the final generation.

Flow:
    User Prompt → [Optimiser LLM] → Optimised Prompt → [Task LLM] → Final Output
"""

from utils import generate_response


def run_prompt_optimizer(user_prompt: str) -> dict:
    """Run the prompt-optimiser pipeline.

    Steps:
        1. Ask the LLM to rewrite/optimise the user's prompt.
        2. Execute the optimised prompt via the LLM to produce the final answer.

    Returns a dict with keys: original_prompt, optimized_prompt, final_output
    """

    # ------------------------------------------------------------------
    # Step 1 — Optimise the prompt
    # ------------------------------------------------------------------
    optimiser_prompt = (
        "You are an expert prompt engineer. Your job is to rewrite a user's "
        "prompt so that it produces the best possible response from an AI "
        "language model.\n\n"
        "Rules for rewriting:\n"
        "- Make the goal crystal-clear and unambiguous.\n"
        "- Add relevant constraints, scope, or success criteria that are "
        "implied but not stated.\n"
        "- Specify the desired output format if it would improve the answer.\n"
        "- Keep the user's original intent intact — do NOT change what they "
        "are asking for.\n"
        "- Return ONLY the rewritten prompt, with no commentary or preamble.\n\n"
        f"Original prompt:\n{user_prompt}"
    )
    optimized_prompt = generate_response(optimiser_prompt)

    # ------------------------------------------------------------------
    # Step 2 — Execute the optimised prompt
    # ------------------------------------------------------------------
    final_output = generate_response(optimized_prompt)

    return {
        "original_prompt": user_prompt,
        "optimized_prompt": optimized_prompt,
        "final_output": final_output,
    }


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    default_prompt = "Tell me about machine learning"
    print(f"Running Prompt Optimizer with prompt: {default_prompt!r}\n")

    result = run_prompt_optimizer(default_prompt)

    print("=" * 60)
    print("ORIGINAL PROMPT")
    print("=" * 60)
    print(result["original_prompt"])
    print()
    print("=" * 60)
    print("OPTIMISED PROMPT")
    print("=" * 60)
    print(result["optimized_prompt"])
    print()
    print("=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(result["final_output"])
