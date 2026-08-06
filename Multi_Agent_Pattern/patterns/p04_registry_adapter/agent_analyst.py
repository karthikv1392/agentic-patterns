"""Analyst Agent — Registry & Adapter pattern.

Registry metadata
-----------------
  capabilities : ["analyse", "evaluate", "compare", "recommend", "strategy",
                  "decision", "trade-offs", "pros-cons", "assess", "plan"]
  best_for     : tasks that need structured reasoning — comparing options,
                 evaluating trade-offs, producing recommendations, or forming strategy.

Role
----
Specialises in structured analysis and decision support. The Analyst takes
raw information or a problem statement and applies frameworks (SWOT, pros/cons,
cost-benefit, etc.) to produce clear recommendations.
"""

from shared.base_agent import BaseAgent

CAPABILITIES = [
    "analyse", "evaluate", "compare", "recommend", "strategy",
    "decision", "trade-offs", "pros-cons", "assess", "plan", "framework",
]

BEST_FOR = [
    "evaluating trade-offs between options",
    "producing structured recommendations",
    "building a strategy or plan",
    "assessing risks and benefits",
    "comparing alternatives with a framework",
]


class AnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Analyst",
            model_name="gemma4",
        )

    @property
    def persona(self) -> str:
        return (
            "You are a sharp strategic analyst who applies structured frameworks "
            "to complex problems and delivers clear, evidence-based recommendations. "
            "Given any problem or dataset you:\n"
            "  • Choose the most appropriate analytical framework (SWOT, cost-benefit, "
            "decision matrix, risk register, etc.).\n"
            "  • Identify key variables, constraints, and trade-offs explicitly.\n"
            "  • Compare options objectively — avoid bias toward any single outcome.\n"
            "  • Produce a prioritised, actionable recommendation with rationale.\n"
            "  • Quantify where possible; qualify where quantification isn't feasible.\n"
            "Your output is a structured analysis with a clear bottom line."
        )
