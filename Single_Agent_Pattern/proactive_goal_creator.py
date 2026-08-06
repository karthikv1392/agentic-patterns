"""Proactive Goal Creator — single-agent pattern demo.

The user provides a goal and optionally uploads an image. The agent enriches
the goal with multi-modal context (image analysis) and environmental context
(current date/time, locale) before executing.
"""

import datetime
import platform

from utils import generate_response, generate_response_with_image


def _gather_env_context() -> str:
    """Collect environmental context: date, time, platform."""
    now = datetime.datetime.now()
    return (
        f"- Current date: {now.strftime('%Y-%m-%d')}\n"
        f"- Current time: {now.strftime('%H:%M:%S')}\n"
        f"- Day of week: {now.strftime('%A')}\n"
        f"- Platform: {platform.system()} {platform.release()}\n"
        f"- Locale/Timezone note: local system time shown above"
    )


def _analyze_image(image_bytes: bytes) -> str:
    """Use Ollama vision to describe / analyze the image."""
    return generate_response_with_image(
        "Describe this image in detail. Identify what it shows, any text, "
        "data, patterns, or notable elements. Be thorough.",
        image_bytes,
    )


def run_proactive(user_prompt: str, image_bytes: bytes | None = None) -> dict:
    """Run the proactive goal creator pipeline.

    Steps:
        1. Gather environmental context.
        2. If an image is provided, analyze it with Gemini vision.
        3. Enrich the original goal with all gathered context.
        4. Execute the enriched goal via LLM.

    Returns a dict with keys: env_context, image_analysis (or None),
    enriched_prompt, final_output
    """

    # Step 1 — Environmental context
    env_context = _gather_env_context()

    # Step 2 — Image analysis (optional)
    image_analysis = None
    if image_bytes:
        image_analysis = _analyze_image(image_bytes)

    # Step 3 — Build enriched prompt
    enriched_parts = [
        "You are an expert assistant. The user has the following goal:\n",
        f'"{user_prompt}"\n',
        "## Environmental Context\n",
        env_context,
        "",
    ]
    if image_analysis:
        enriched_parts.append("## Image Analysis\n")
        enriched_parts.append(
            "The user provided an image. Here is a detailed analysis:\n"
        )
        enriched_parts.append(image_analysis)
        enriched_parts.append("")

    enriched_parts.append(
        "Using ALL of the context above (environmental info"
        + (" and image analysis" if image_analysis else "")
        + "), provide a comprehensive, actionable response to the user's goal. "
        "Tailor your answer to the context provided. Use markdown formatting."
    )
    enriched_prompt = "\n".join(enriched_parts)

    # Step 4 — Execute
    final_output = generate_response(enriched_prompt)

    return {
        "env_context": env_context,
        "image_analysis": image_analysis,
        "enriched_prompt": enriched_prompt,
        "final_output": final_output,
    }


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    default_prompt = "What should I focus on today to be productive?"
    print(f"Running Proactive Goal Creator with prompt: {default_prompt!r}\n")
    print("(No image provided in standalone mode)\n")

    result = run_proactive(default_prompt)

    print("=" * 60)
    print("ENVIRONMENTAL CONTEXT")
    print("=" * 60)
    print(result["env_context"])
    print()
    print("=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(result["final_output"])
