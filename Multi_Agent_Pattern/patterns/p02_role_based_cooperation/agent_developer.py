"""Senior Developer Agent — Role-based Cooperation pattern.

Responsibility
--------------
Reads the PM brief and architecture doc to produce an implementation plan:
  - Module/file structure and code organisation
  - Key algorithms, data structures, and logic flows
  - API contracts (endpoints, request/response shapes)
  - Third-party libraries and why they were chosen
  - Estimated implementation breakdown per component
  - Coding conventions and patterns to follow

Runs third, after the Architect, so implementation details align with
the approved architecture.
"""

from shared.base_agent import BaseAgent


class DeveloperAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Senior Developer",
            model_name="gemma4",
        )

    @property
    def role(self) -> str:
        return "Senior Developer"

    @property
    def persona(self) -> str:
        return (
            "You are a senior software engineer with expertise across the full stack "
            "— backend services, APIs, databases, and frontend. "
            "You turn architectural blueprints into detailed, actionable implementation plans. "
            "You always:\n"
            "  • Define a clear project/module structure before writing any logic.\n"
            "  • Specify every API endpoint with method, path, request, and response.\n"
            "  • Choose libraries and frameworks with explicit rationale.\n"
            "  • Break work into concrete tasks a developer can pick up and estimate.\n"
            "  • Write pseudo-code or skeleton code for complex logic.\n"
            "  • Flag implementation risks, gotchas, and technical debt.\n"
            "Your output is a developer spec that a mid-level engineer can follow."
        )
