"""Researcher Agent — Registry & Adapter pattern.

Registry metadata
-----------------
  capabilities : ["research", "facts", "information", "explore", "investigate",
                  "background", "literature", "sources", "evidence"]
  best_for     : tasks that need facts gathered, topics explored in depth,
                 or background knowledge assembled before other work begins.

Role
----
Specialises in deep information gathering. Given a topic or question,
the Researcher surfaces relevant facts, context, examples, and open
questions — acting as the information foundation for downstream agents.
"""

from shared.base_agent import BaseAgent

CAPABILITIES = [
    "research", "facts", "information", "explore", "investigate",
    "background", "literature", "sources", "evidence", "context",
]

BEST_FOR = [
    "gathering background information",
    "answering factual questions",
    "exploring a topic in depth",
    "finding relevant examples and evidence",
]


class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Researcher",
            model_name="gemma4",
        )

    @property
    def persona(self) -> str:
        return (
            "You are a rigorous research specialist with expertise in gathering, "
            "evaluating, and synthesising information across domains. "
            "Given any topic or question you:\n"
            "  • Surface the most relevant facts, data points, and context.\n"
            "  • Cite known examples, case studies, or historical precedents.\n"
            "  • Distinguish between well-established knowledge and open questions.\n"
            "  • Organise findings clearly — use headers, bullets, and sections.\n"
            "  • Flag gaps in available knowledge or areas of ongoing debate.\n"
            "Your output is a well-structured research brief."
        )
