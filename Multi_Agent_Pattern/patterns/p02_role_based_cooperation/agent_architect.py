"""System Architect Agent — Role-based Cooperation pattern.

Responsibility
--------------
Reads the PM's product brief and produces a high-level technical blueprint:
  - Recommended tech stack with rationale
  - System components and how they interact (service diagram in text)
  - Data models and storage strategy
  - Key architectural decisions and trade-offs
  - Non-functional requirements: scalability, security, availability
  - Integration points and external dependencies

Runs second, after the Product Manager, so the architecture is grounded
in the actual product scope.
"""

from shared.base_agent import BaseAgent


class ArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="System Architect",
            model_name="gemma4",
        )

    @property
    def role(self) -> str:
        return "System Architect"

    @property
    def persona(self) -> str:
        return (
            "You are a principal System Architect with deep expertise in "
            "distributed systems, cloud infrastructure, and software design patterns. "
            "You translate product requirements into technical blueprints. "
            "You always:\n"
            "  • Choose the simplest architecture that meets the requirements.\n"
            "  • Justify every technology choice with explicit trade-offs.\n"
            "  • Draw system diagrams using ASCII or structured text.\n"
            "  • Define clear component boundaries and interfaces (APIs, events, etc.).\n"
            "  • Address scalability, security, and fault-tolerance from the start.\n"
            "  • Flag technical risks and propose mitigation strategies.\n"
            "Your output is a technical design document that developers can implement."
        )
