"""QA Engineer Agent — Role-based Cooperation pattern.

Responsibility
--------------
Reviews all prior outputs (PM brief, architecture, implementation plan) and
produces a comprehensive quality strategy:
  - Test plan: unit, integration, E2E, performance
  - Critical test cases per feature / acceptance criterion
  - Edge cases, boundary conditions, and error scenarios
  - Non-functional testing: load, security, accessibility
  - Definition of Done and release checklist
  - Known risks that need extra coverage

Runs last in the pipeline, with full context from all prior agents,
so nothing falls through the cracks.
"""

from shared.base_agent import BaseAgent


class QAEngineerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="QA Engineer",
            model_name="gemma4",
        )

    @property
    def role(self) -> str:
        return "QA Engineer"

    @property
    def persona(self) -> str:
        return (
            "You are a senior QA Engineer and quality advocate with expertise in "
            "test strategy, automation, and risk-based testing. "
            "You ensure that software ships with confidence. "
            "You always:\n"
            "  • Map every acceptance criterion to at least one test case.\n"
            "  • Think adversarially — what could go wrong? What would a user break?\n"
            "  • Cover happy paths, edge cases, and failure scenarios.\n"
            "  • Specify which tests should be automated vs manual and why.\n"
            "  • Define performance benchmarks and security test areas.\n"
            "  • Produce a clear Definition of Done and go/no-go checklist.\n"
            "Your output is a quality plan that gives the team confidence to ship."
        )
