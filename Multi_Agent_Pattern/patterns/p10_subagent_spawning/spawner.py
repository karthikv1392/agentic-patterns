"""Spawner Agent — analyzes the task and dynamically generates sub-agent specifications.

The SpawnerAgent is the orchestrator of the Sub-Agent Spawning pattern.
Unlike p05's Initiator which uses fixed agent roles (Researcher, Analyst, etc.),
the Spawner:
  1. Analyzes the task and domain context.
  2. Decides HOW MANY sub-agents are needed (up to max_subagents).
  3. Generates a CUSTOM name, persona, and scoped task for each sub-agent.
  4. Returns specs that the executor uses to instantiate SubAgent objects at runtime.

This is the core distinction from static fan-out: sub-agents don't exist
until the Spawner creates their specifications in response to a specific task.
"""

import json
import re

from shared.base_agent import BaseAgent
from shared.llm import generate_response


DOMAIN_GUIDANCE = {
    "Code Migration": (
        "You are decomposing a CODE MIGRATION task. "
        "Each sub-agent should own a distinct component, module, or layer of the codebase "
        "(e.g., 'Route Handler Migrator', 'Database Model Converter', 'Auth Middleware Adapter', "
        "'Test Suite Updater'). Give each agent a precise, technical persona and a scoped task "
        "that covers one cohesive slice of the migration without overlapping with others. "
        "The focus_area should name the specific file(s) or subsystem the agent handles."
    ),
    "Code Transformation": (
        "You are decomposing a CODE TRANSFORMATION task (refactoring, modernisation, or "
        "adding cross-cutting concerns). Each sub-agent should own a specific transformation "
        "type or module group (e.g., 'Type Annotation Specialist', 'Async Converter', "
        "'Error Handling Refactorer', 'Performance Optimizer'). Persona should reflect deep "
        "expertise in that specific transformation technique."
    ),
    "Document Analysis": (
        "You are decomposing a DOCUMENT ANALYSIS task. Each sub-agent should cover a distinct "
        "section, dimension, or analytical lens (e.g., 'Executive Summary Analyst', "
        "'Technical Depth Reviewer', 'Risk & Assumptions Auditor', 'Data Quality Checker'). "
        "Persona should reflect the specific analytical skill required."
    ),
    "System Design": (
        "You are decomposing a SYSTEM DESIGN task. Each sub-agent should design one service, "
        "layer, or cross-cutting concern (e.g., 'API Gateway Designer', 'Data Storage Architect', "
        "'Auth & Identity Service Designer', 'Observability & Monitoring Designer'). "
        "Persona should reflect a senior architect specialising in that domain."
    ),
}


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


class SpawnerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Spawner", model_name="gemma4")

    @property
    def persona(self) -> str:
        return (
            "You are a master orchestrator specialising in dynamic task decomposition. "
            "Given a complex task, you identify the optimal set of specialist sub-agents "
            "to spawn — each with a unique identity, custom persona, and precisely scoped "
            "work assignment. You think in terms of independence, parallelism, and cohesion."
        )

    def analyze_and_spawn(
        self, task: str, domain: str, max_subagents: int = 5
    ) -> dict:
        """Analyze the task and produce sub-agent specifications.

        Parameters
        ----------
        task          : The complex task to decompose.
        domain        : Domain hint for decomposition strategy.
        max_subagents : Upper bound on spawned agents (2-6).

        Returns
        -------
        {
            "strategy"     : str,         — overall decomposition approach
            "rationale"    : str,         — why this decomposition makes sense
            "num_agents"   : int,         — actual count decided by the LLM
            "subagent_specs": [
                {
                    "id"         : int,
                    "name"       : str,   — e.g. "Flask Routes Migrator"
                    "role"       : str,   — e.g. "Routes Migration Specialist"
                    "persona"    : str,   — full system prompt for this agent
                    "task"       : str,   — scoped work assignment
                    "focus_area" : str,   — specific file / subsystem / dimension
                },
                ...
            ],
            "synthesis_hint": str,        — guidance for the synthesizer
        }
        """
        domain_ctx = DOMAIN_GUIDANCE.get(domain, DOMAIN_GUIDANCE["Code Transformation"])
        n = min(max(2, max_subagents), 6)

        prompt = (
            f"{self.persona}\n\n"
            f"Domain context:\n{domain_ctx}\n\n"
            f"Task to decompose:\n{task}\n\n"
            f"Spawn between 2 and {n} sub-agents (choose the right number for this task, "
            f"do not just use the maximum).\n\n"
            "For each sub-agent:\n"
            "  • name       — a specific, evocative title (e.g. 'SQLAlchemy Model Migrator')\n"
            "  • role       — concise role label (e.g. 'Database Migration Specialist')\n"
            "  • persona    — 2-3 sentence system prompt that shapes their reasoning style\n"
            "  • task       — precise, self-contained work assignment (no cross-dependencies)\n"
            "  • focus_area — the specific component/file/section this agent owns\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "strategy": "one-sentence decomposition approach",\n'
            '  "rationale": "2-3 sentences explaining the decomposition",\n'
            '  "num_agents": <integer>,\n'
            '  "subagent_specs": [\n'
            '    {\n'
            '      "id": 1,\n'
            '      "name": "...",\n'
            '      "role": "...",\n'
            '      "persona": "...",\n'
            '      "task": "...",\n'
            '      "focus_area": "..."\n'
            '    }\n'
            "  ],\n"
            '  "synthesis_hint": "brief instruction for how to integrate all outputs"\n'
            "}"
        )

        raw = generate_response(prompt, model_name=self.model_name)
        data = _extract_json(raw)

        if not data.get("subagent_specs"):
            # Fallback: generic 3-agent split
            data = self._fallback_specs(task, domain, min(3, n))

        # Clamp to max_subagents
        specs = data["subagent_specs"][:n]
        for i, spec in enumerate(specs, 1):
            spec["id"] = i

        data["subagent_specs"] = specs
        data["num_agents"] = len(specs)
        return data

    @staticmethod
    def _fallback_specs(task: str, domain: str, n: int) -> dict:
        labels = [
            ("Analyzer", "Analysis Specialist",
             "You are a thorough analyst. Break down the given component systematically."),
            ("Implementer", "Implementation Specialist",
             "You are a precise implementer. Produce clean, well-structured output."),
            ("Validator", "Validation Specialist",
             "You are a rigorous validator. Identify edge cases and ensure correctness."),
        ][:n]
        return {
            "strategy": f"Generic {n}-way decomposition of the {domain} task.",
            "rationale": "Fallback decomposition used due to parsing error.",
            "num_agents": n,
            "subagent_specs": [
                {
                    "id": i + 1,
                    "name": name,
                    "role": role,
                    "persona": persona,
                    "task": f"[{name}] Work on your assigned portion of: {task}",
                    "focus_area": f"Part {i + 1}",
                }
                for i, (name, role, persona) in enumerate(labels)
            ],
            "synthesis_hint": "Integrate all outputs into a coherent whole.",
        }
