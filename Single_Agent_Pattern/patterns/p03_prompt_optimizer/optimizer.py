"""Prompt optimiser — isolated LLM call.

Separated from agent.py so learners can see that prompt optimisation
is itself just an LLM call with a carefully crafted meta-prompt.
"""

from shared.llm import generate_response


def optimize(user_prompt: str) -> str:
    """Rewrite *user_prompt* to be clearer, more specific, and better structured.

    Rules enforced via the meta-prompt:
      - Keep the user's original intent intact.
      - Add implied constraints / success criteria.
      - Specify output format where helpful.
      - Return ONLY the rewritten prompt, no commentary.
    """
    meta_prompt = (
        "You are an expert prompt engineer. Rewrite the following user prompt "
        "so that it produces the best possible response from an AI language model.\n\n"
        "Rules:\n"
        "- Make the goal crystal-clear and unambiguous.\n"
        "- Add relevant constraints or success criteria that are implied.\n"
        "- Specify the desired output format if it would improve the answer.\n"
        "- Do NOT change what the user is asking for.\n"
        "- Return ONLY the rewritten prompt — no commentary or preamble.\n\n"
        f"Original prompt:\n{user_prompt}"
    )
    return generate_response(meta_prompt)
