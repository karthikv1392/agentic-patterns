"""Writer Agent — Registry & Adapter pattern.

Registry metadata
-----------------
  capabilities : ["write", "draft", "explain", "document", "content",
                  "narrative", "prose", "blog", "report", "communicate"]
  best_for     : tasks that need well-structured written output — explanations,
                 reports, blog posts, documentation, executive summaries.

Role
----
Specialises in turning information and analysis into clear, engaging
written content. The Writer consumes research/analysis from prior steps
and produces polished, audience-appropriate prose.
"""

from shared.base_agent import BaseAgent

CAPABILITIES = [
    "write", "draft", "explain", "document", "content",
    "narrative", "prose", "blog", "report", "communicate", "articulate",
]

BEST_FOR = [
    "writing reports or documents",
    "drafting blog posts or articles",
    "explaining concepts clearly",
    "producing executive summaries",
    "creating audience-appropriate content",
]


class WriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Writer",
            model_name="gemma4",
        )

    @property
    def persona(self) -> str:
        return (
            "You are an expert writer and communicator who transforms complex "
            "information into clear, engaging, well-structured prose. "
            "Given any content or brief you:\n"
            "  • Adapt tone and style to the intended audience.\n"
            "  • Structure output with logical flow: intro → body → conclusion.\n"
            "  • Use concrete examples to make abstract points tangible.\n"
            "  • Prefer active voice, short sentences, and plain language.\n"
            "  • Use markdown formatting (headers, bullets, bold) to aid readability.\n"
            "Your output is polished, publication-ready written content."
        )
