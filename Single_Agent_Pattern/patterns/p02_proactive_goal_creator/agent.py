"""Proactive Goal Creator — agent.

The user provides a goal (and optionally an image). The agent:
  1. Gathers environmental context (date, time, platform)  via context.py
  2. Analyses the image (if provided)                      via context.py
  3. Builds an enriched prompt combining goal + all context
  4. Executes the enriched prompt via the LLM

Unlike the Passive Goal Creator, this agent *proactively* collects
extra context before calling the LLM — hence "proactive".
"""

from shared.llm import generate_response
from patterns.p02_proactive_goal_creator.context import gather_env_context, analyze_image


def run(user_prompt: str, image_bytes: bytes | None = None) -> dict:
    """
    Args:
        user_prompt : The user's goal or task.
        image_bytes : Optional raw image bytes for multi-modal context.

    Returns:
        env_context    : Collected environment info string
        image_analysis : Vision-model description (or None)
        final_output   : LLM response enriched with all context
    """

    # Step 1: environmental context
    env_context = gather_env_context()

    # Step 2: image analysis (optional)
    image_analysis = analyze_image(image_bytes) if image_bytes else None

    # Step 3: build enriched prompt
    parts = [
        "You are an expert assistant. The user has the following goal:\n",
        f'"{user_prompt}"\n',
        "## Environmental Context\n",
        env_context, "",
    ]
    if image_analysis:
        parts += ["## Image Analysis\n", image_analysis, ""]
    parts.append(
        "Using ALL of the context above, provide a comprehensive, actionable "
        "response to the user's goal. Use markdown formatting."
    )
    enriched_prompt = "\n".join(parts)

    # Step 4: execute
    final_output = generate_response(enriched_prompt)

    return {
        "env_context": env_context,
        "image_analysis": image_analysis,
        "final_output": final_output,
    }
