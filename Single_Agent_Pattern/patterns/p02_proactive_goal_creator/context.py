"""Context gatherers for the Proactive Goal Creator.

Separated from agent.py so learners can clearly see what
"proactive context enrichment" means in practice.
"""

import datetime
import platform

from shared.llm import generate_response_with_image


def gather_env_context() -> str:
    """Return a YAML-style block of current environment information."""
    now = datetime.datetime.now()
    return (
        f"- Current date: {now.strftime('%Y-%m-%d')}\n"
        f"- Current time: {now.strftime('%H:%M:%S')}\n"
        f"- Day of week: {now.strftime('%A')}\n"
        f"- Platform: {platform.system()} {platform.release()}\n"
        f"- Locale/Timezone note: local system time shown above"
    )


def analyze_image(image_bytes: bytes) -> str:
    """Use Ollama vision to describe and analyse an uploaded image."""
    return generate_response_with_image(
        "Describe this image in detail. Identify what it shows, any text, "
        "data, patterns, or notable elements. Be thorough.",
        image_bytes,
    )
