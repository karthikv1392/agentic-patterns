"""Sub-Agent — dynamically instantiated at runtime from a spawner specification.

Unlike pre-defined agents (p05 Researcher, Analyst, etc.), SubAgent objects are
created entirely at runtime. Their name, persona, and task all come from the
SpawnerAgent's LLM output, making each instance unique to the specific task.

Usage
-----
spec = {
    "id":         1,
    "name":       "Flask Routes Migrator",
    "role":       "Routes Migration Specialist",
    "persona":    "You are an expert in Flask and FastAPI...",
    "task":       "Migrate all @app.route decorators to FastAPI path operations...",
    "focus_area": "routes.py, blueprints/",
}
agent = SubAgent(spec)
result = agent.execute_task()
"""

import time

from shared.base_agent import BaseAgent
from shared.llm import generate_response


class SubAgent(BaseAgent):
    """A dynamically spawned specialist agent.

    Every attribute — name, persona, task — is set at instantiation time
    from a spec dict produced by the SpawnerAgent. No SubAgent class is
    ever imported or used before the Spawner decides it is needed.
    """

    def __init__(self, spec: dict):
        super().__init__(name=spec["name"], model_name="gemma4")
        self._persona_text = spec["persona"]
        self.spec          = spec
        self.agent_id      = spec["id"]
        self._role_label   = spec["role"]
        self.assigned_task = spec["task"]
        self.focus_area    = spec["focus_area"]

    @property
    def persona(self) -> str:
        return self._persona_text

    @property
    def role(self) -> str:
        return self._role_label

    def execute_task(self) -> dict:
        """Execute the scoped task assigned by the Spawner.

        Returns
        -------
        {
            "agent_id"   : int,
            "name"       : str,
            "role"       : str,
            "focus_area" : str,
            "task"       : str,
            "output"     : str,
            "latency_s"  : float,
        }
        """
        prompt = (
            f"{self._persona_text}\n\n"
            f"Your assigned focus area: {self.focus_area}\n\n"
            f"Your task:\n{self.assigned_task}\n\n"
            "Deliver your complete, expert output. Be specific and thorough. "
            "Use markdown formatting where it aids clarity."
        )

        start = time.time()
        output = generate_response(prompt, model_name=self.model_name)
        elapsed = round(time.time() - start, 2)

        return {
            "agent_id":   self.agent_id,
            "name":       self.name,
            "role":       self.role,
            "focus_area": self.focus_area,
            "task":       self.assigned_task,
            "output":     output,
            "latency_s":  elapsed,
        }
