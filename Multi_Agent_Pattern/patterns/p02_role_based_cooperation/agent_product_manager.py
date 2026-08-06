"""Product Manager Agent — Role-based Cooperation pattern.

Responsibility
--------------
Translates the user's raw need into a clear product definition:
  - Goals and success criteria
  - User personas and key use-cases
  - Scope: what's in / what's explicitly out
  - Prioritised feature list (MoSCoW or similar)
  - Open questions that downstream roles should address

Runs first in the pipeline so every subsequent agent starts from a
well-scoped product brief rather than a vague prompt.
"""

from shared.base_agent import BaseAgent


class ProductManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Product Manager",
            model_name="gemma4",
        )

    @property
    def role(self) -> str:
        return "Product Manager"

    @property
    def persona(self) -> str:
        return (
            "You are a seasoned Product Manager with 10+ years of experience "
            "shipping successful software products. "
            "Your job is to transform ambiguous requests into a crisp product brief. "
            "You always:\n"
            "  • Define the problem before jumping to solutions.\n"
            "  • Identify the primary user persona and their core pain-points.\n"
            "  • Write clear, testable acceptance criteria for every feature.\n"
            "  • Scope ruthlessly — explicitly list what is OUT of scope.\n"
            "  • Highlight risks, assumptions, and open questions.\n"
            "  • Prioritise using MoSCoW (Must / Should / Could / Won't).\n"
            "Your output is a product brief that engineers and designers can act on immediately."
        )
