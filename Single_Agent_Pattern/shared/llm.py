"""Shared LLM client — wraps Ollama (local inference).

All patterns import from here so the model configuration lives in one place.
"""

import ollama

MODEL = "gemma4"


def generate_response(prompt: str, model_name: str = MODEL) -> str:
    """Generate a text response for the given prompt."""
    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.message.content


def generate_response_with_image(prompt: str, image_bytes: bytes, model_name: str = MODEL) -> str:
    """Generate a response for a prompt that includes an image."""
    response = ollama.chat(
        model=model_name,
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image_bytes],
        }],
    )
    return response.message.content
