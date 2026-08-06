"""
config.py - Letta client setup

Supports two modes:
  1. Cloud (default): Set LETTA_API_KEY in your .env
     Sign up at: https://app.letta.com

  2. Local server: Set LETTA_BASE_URL=http://localhost:8283
     Run locally via Docker (Gemini):
       docker run -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
                  -p 8283:8283 \
                  -e GEMINI_API_KEY="AIza..." \
                  letta/letta:latest
"""

import os
from dotenv import load_dotenv
from letta_client import Letta

load_dotenv()


def get_client() -> Letta:
    """Return a Letta client (cloud or local)."""
    base_url = os.getenv("LETTA_BASE_URL")
    api_key  = os.getenv("LETTA_API_KEY")

    if base_url:
        # Local server — no API key needed
        print(f"[config] Connecting to local Letta server: {base_url}")
        return Letta(base_url=base_url)
    elif api_key:
        # Letta Cloud
        print("[config] Connecting to Letta Cloud")
        return Letta(token=api_key)
    else:
        raise EnvironmentError(
            "Set either LETTA_API_KEY (cloud) or LETTA_BASE_URL (local) in your .env file.\n"
            "Cloud: https://app.letta.com\n"
            "Local: docker run -p 8283:8283 -e OPENAI_API_KEY=sk-... letta/letta:latest"
        )


# Default model — using Google Gemini via local Letta server
DEFAULT_MODEL     = os.getenv("LETTA_MODEL", "google_ai/gemini-2.5-flash")
DEFAULT_EMBEDDING = os.getenv("LETTA_EMBEDDING", "letta/letta-free")
