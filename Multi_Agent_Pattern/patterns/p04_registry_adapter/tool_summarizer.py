"""Summarizer Tool — Registry & Adapter pattern.

Registry metadata
-----------------
  capabilities : ["summarise", "condense", "tldr", "shorten", "bullets",
                  "key-points", "overview", "abstract", "digest"]
  best_for     : condensing long text into key points, producing TL;DRs,
                 creating executive summaries from verbose content.

Implementation
--------------
LLM-based: receives a task (which may include content to summarise)
and returns a structured bullet-point summary.
"""

from shared.base_tool import BaseTool
from shared.llm import generate_response

CAPABILITIES = [
    "summarise", "condense", "tldr", "shorten", "bullets",
    "key-points", "overview", "abstract", "digest", "compress",
]

BEST_FOR = [
    "condensing long content into key points",
    "producing TL;DR overviews",
    "creating bullet-point summaries",
    "extracting the most important information",
]


class SummarizerTool(BaseTool):
    @property
    def name(self) -> str:
        return "Summarizer"

    @property
    def description(self) -> str:
        return (
            "Condenses any content or task into a concise, structured bullet-point "
            "summary highlighting the most important points."
        )

    @property
    def capabilities(self) -> list[str]:
        return CAPABILITIES

    def run(self, task: str) -> str:
        prompt = (
            "You are a precise summarisation tool. "
            "Given the following task or content, produce a concise structured summary:\n\n"
            f"{task}\n\n"
            "Format your output as:\n"
            "**Key Points:**\n"
            "• [point 1]\n"
            "• [point 2]\n"
            "...\n\n"
            "**Bottom Line:** [one sentence conclusion]\n\n"
            "Be concise — quality over quantity."
        )
        return generate_response(prompt)
