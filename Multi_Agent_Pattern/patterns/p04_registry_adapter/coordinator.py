"""Coordinator Agent — Registry & Adapter pattern.

The Coordinator is the entry point for every user task. It is an LLM-based
agent whose sole job is to read both registries and decide HOW to solve the task:

  1. Receive the task.
  2. Read the full AgentRegistry catalogue (who can reason about what).
  3. Read the full ToolRegistry catalogue (what deterministic tools exist).
  4. In a single LLM call, produce:
       - An explanation of its reasoning (why these choices, in this order).
       - An ordered execution plan: each step names one agent or tool,
         which registry it comes from, and the specific sub-task to perform.

Why a coordinator agent rather than a plain function?
------------------------------------------------------
A plain query() function treats registry selection as a mechanical match.
A coordinator REASONS about the task: it can decide that a tool should run
BEFORE an agent (e.g. extract keywords first, then write about them), or
that two agents should combine efforts, or that no tool is needed at all.
It can also explain its choices — making the system interpretable.
"""

import json
import re

from shared.base_agent import BaseAgent
from shared.llm        import generate_response
from patterns.p04_registry_adapter.registry import AgentRegistry, ToolRegistry


class CoordinatorAgent(BaseAgent):
    """LLM agent that queries both registries and builds the execution plan."""

    def __init__(self):
        super().__init__(
            name="Coordinator",
            model_name="gemma4",
        )

    @property
    def persona(self) -> str:
        return (
            "You are an intelligent task coordinator in a multi-agent system. "
            "Your job is to analyse an incoming task, inspect the available agents "
            "and tools in two separate registries, and produce the optimal execution "
            "plan that assigns the right agent or tool to each part of the work.\n"
            "You think step-by-step, choose the minimal set of agents/tools needed, "
            "and always order them logically (gather information before writing, "
            "compute before analysing, etc.)."
        )

    def coordinate(
        self,
        task:             str,
        agent_registry:   AgentRegistry,
        tool_registry:    ToolRegistry,
    ) -> dict:
        """Inspect both registries and build an execution plan for *task*.

        Parameters
        ----------
        task           : the user's natural-language task
        agent_registry : registry of LLM-based agents
        tool_registry  : registry of deterministic tools

        Returns
        -------
        {
            "reasoning" : str         — why these choices, in this order
            "plan"      : list[dict]  — [{"name", "registry", "sub_task"}, ...]
                          registry is "agent" | "tool"
        }
        """
        agents_block = self._format_catalogue(agent_registry.all_metadata(), "AGENT REGISTRY")
        tools_block  = self._format_catalogue(tool_registry.all_metadata(),  "TOOL REGISTRY")

        all_agent_names = [e["name"] for e in agent_registry.all_metadata()]
        all_tool_names  = [e["name"] for e in tool_registry.all_metadata()]

        prompt = (
            f"{self.persona}\n\n"
            f"TASK:\n{task}\n\n"
            f"{agents_block}\n\n"
            f"{tools_block}\n\n"
            "INSTRUCTIONS:\n"
            "1. Decide which agents and/or tools are needed (use the minimum necessary).\n"
            "2. Order them logically — later steps may build on earlier outputs.\n"
            "3. Assign each a specific, focused sub-task (2-3 sentences).\n"
            "4. Explain your overall reasoning.\n\n"
            f"Valid agent names: {all_agent_names}\n"
            f"Valid tool names:  {all_tool_names}\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "reasoning": "your step-by-step explanation",\n'
            '  "plan": [\n'
            '    {"name": "<exact name>", "registry": "agent" or "tool", '
            '"sub_task": "<specific instruction>"},\n'
            "    ...\n"
            "  ]\n"
            "}"
        )

        raw  = generate_response(prompt, model_name=self.model_name)
        data = self._extract_json(raw)

        # Validate plan entries — drop any with unknown names
        valid_names = set(all_agent_names + all_tool_names)
        raw_plan    = data.get("plan", [])
        plan = [
            step for step in raw_plan
            if isinstance(step, dict) and step.get("name") in valid_names
        ]

        # Fallback: if plan is empty, use all agents in order
        if not plan:
            plan = [
                {"name": n, "registry": "agent", "sub_task": task}
                for n in all_agent_names[:3]
            ]

        return {
            "reasoning": data.get("reasoning", ""),
            "plan":      plan,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_catalogue(metadata: list[dict], header: str) -> str:
        lines = [f"--- {header} ---"]
        for entry in metadata:
            lines.append(
                f"Name: {entry['name']}\n"
                f"Description: {entry['description']}\n"
                f"Best for: {'; '.join(entry.get('best_for', []))}"
            )
        return "\n\n".join(lines)

    @staticmethod
    def _extract_json(text: str) -> dict:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}
