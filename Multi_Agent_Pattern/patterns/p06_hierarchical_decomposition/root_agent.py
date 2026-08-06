"""Root Agent — Level 0 (apex) in the 3-tier hierarchy.

The Root Agent is the strategic brain of the entire pipeline. It:
  1. Receives the complex, open-ended task from the user.
  2. Uses an LLM call to perform high-level decomposition into N domain areas.
     Each domain becomes the responsibility of one Mid-level Agent.
  3. After all mid-level agents complete, collects their domain syntheses.
  4. Performs a final cross-domain LLM synthesis to produce the definitive answer.

The Root Agent deliberately operates at a high level of abstraction —
it does NOT do the domain research itself. Its value is in asking the right
questions and weaving the answers together.
"""

import json
import re

from shared.base_agent import BaseAgent
from shared.llm import generate_response


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


class RootAgent(BaseAgent):
    """Apex orchestrator: decomposes into domains, then synthesises all outputs.

    This is the only agent that sees both the raw task and the final
    integrated picture. Everything in between is handled by mid-level
    and worker agents through delegation.
    """

    def __init__(self):
        super().__init__(name="Root Orchestrator", model_name="gemma4")

    @property
    def persona(self) -> str:
        return (
            "You are a senior research director with expertise in breaking down "
            "complex, multi-dimensional problems. You think at the strategic level: "
            "identifying the key domains that must be investigated, framing precise "
            "research directives for domain teams, and synthesising their findings "
            "into authoritative, executive-level reports."
        )

    @property
    def tier(self) -> str:
        return "root"

    # ------------------------------------------------------------------
    # Step 1 — High-level decomposition into domain areas
    # ------------------------------------------------------------------

    def decompose(self, task: str, num_domains: int = 3) -> dict:
        """Decompose the complex task into N independent domain areas.

        Parameters
        ----------
        task        : The complex open-ended task from the user.
        num_domains : How many domain areas (mid-level agents) to create.

        Returns
        -------
        {
            "overview" : str  — decomposition rationale
            "domains"  : [
                {
                    "index"       : int  — 1-based
                    "name"        : str  — short domain label (3-5 words)
                    "description" : str  — what this domain covers
                    "task"        : str  — directive for the mid-level agent
                },
                ...
            ]
        }
        """
        prompt = (
            f"{self.persona}\n\n"
            "You have received the following complex research task:\n"
            f"{task}\n\n"
            f"Decompose it into exactly {num_domains} high-level domain areas. "
            "Each domain must:\n"
            "  • Cover a distinct, non-overlapping dimension of the problem.\n"
            "  • Be independently researchable (no dependencies between domains).\n"
            "  • Include a specific 2-3 sentence research directive for the domain team.\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "overview": "one-paragraph strategy: why these domains, how they cover the problem",\n'
            '  "domains": [\n'
            '    {\n'
            '      "index": 1,\n'
            '      "name": "Domain Name (3-5 words)",\n'
            '      "description": "what this domain covers (1 sentence)",\n'
            '      "task": "specific research directive for the mid-level team (2-3 sentences)"\n'
            '    },\n'
            "    ...\n"
            "  ]\n"
            "}"
        )
        raw = generate_response(prompt, model_name=self.model_name)
        data = _extract_json(raw)

        if data.get("domains") and len(data["domains"]) >= num_domains:
            return data

        # Fallback: generic domain split
        default_domains = [
            "Background & Foundations",
            "Current State & Landscape",
            "Future Implications & Recommendations",
        ][:num_domains]
        return {
            "overview": (
                f"Decomposing the task into {num_domains} core research domains "
                "to ensure comprehensive coverage."
            ),
            "domains": [
                {
                    "index":       i + 1,
                    "name":        name,
                    "description": f"Research the {name.lower()} of the topic.",
                    "task": (
                        f"Research the {name.lower()} of the following topic in depth: {task}"
                    ),
                }
                for i, name in enumerate(default_domains)
            ],
        }

    # ------------------------------------------------------------------
    # Step 6 — Final cross-domain synthesis
    # ------------------------------------------------------------------

    def synthesise(
        self,
        task: str,
        domain_syntheses: dict[str, str],
    ) -> str:
        """Produce the final comprehensive answer from all domain reports.

        Parameters
        ----------
        task             : The original user task.
        domain_syntheses : {domain_name -> domain_synthesis_text}
        """
        domain_block = "\n\n".join(
            f"══ {name} ══\n{synthesis}"
            for name, synthesis in domain_syntheses.items()
        )
        prompt = (
            f"{self.persona}\n\n"
            "Original research task:\n"
            f"{task}\n\n"
            "Your domain teams have completed their research. "
            "Their domain reports:\n\n"
            f"{domain_block}\n\n"
            "Now produce the definitive final report. It must:\n"
            "  1. Open with an executive summary (3-4 sentences).\n"
            "  2. Integrate the most important cross-domain findings and connections.\n"
            "  3. Present key insights under clear headings.\n"
            "  4. Close with conclusions and actionable recommendations.\n\n"
            "This is the authoritative answer to the original task. "
            "Use markdown. 600-900 words."
        )
        return generate_response(prompt, model_name=self.model_name)
