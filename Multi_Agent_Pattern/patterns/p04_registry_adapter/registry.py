"""Agent Registry & Tool Registry — Registry & Adapter pattern.

Two separate, typed registries keep concerns clearly separated:

  AgentRegistry  — stores BaseAgent subclasses (LLM-based reasoning)
  ToolRegistry   — stores BaseTool subclasses  (deterministic computation)

Why separate?
-------------
Mixing agents and tools in one registry blurs the most important distinction
in the pattern: agents reason with LLMs, tools compute deterministically.
Separate registries let the CoordinatorAgent make explicit, informed choices
from each catalogue — and make it trivial to add new agents or tools without
touching anything else.

Both classes share the same interface so the CoordinatorAgent can read
their catalogues uniformly via `all_metadata()`.
"""

from shared.base_agent import BaseAgent
from shared.base_tool  import BaseTool


class AgentRegistry:
    """Registry for LLM-based agents (BaseAgent subclasses) only."""

    def __init__(self):
        self._entries: dict[str, dict] = {}

    def register(
        self,
        agent: BaseAgent,
        description:  str,
        capabilities: list[str],
        best_for:     list[str],
    ) -> None:
        """Register an agent. Raises TypeError if obj is not a BaseAgent."""
        if not isinstance(agent, BaseAgent):
            raise TypeError(
                f"AgentRegistry only accepts BaseAgent subclasses, "
                f"got {type(agent).__name__}. Use ToolRegistry for tools."
            )
        self._entries[agent.name] = {
            "name":         agent.name,
            "entry_type":   "agent",
            "description":  description,
            "capabilities": capabilities,
            "best_for":     best_for,
            "model":        agent.model_name,
            "obj":          agent,
        }

    def all_metadata(self) -> list[dict]:
        """Return metadata for all registered agents (no obj reference)."""
        return [{k: v for k, v in e.items() if k != "obj"}
                for e in self._entries.values()]

    def get(self, name: str) -> BaseAgent:
        return self._entries[name]["obj"]

    def get_entry(self, name: str) -> dict:
        return self._entries[name]

    def __contains__(self, name: str) -> bool:
        return name in self._entries

    def __len__(self) -> int:
        return len(self._entries)


class ToolRegistry:
    """Registry for deterministic tools (BaseTool subclasses) only."""

    def __init__(self):
        self._entries: dict[str, dict] = {}

    def register(
        self,
        tool:         BaseTool,
        description:  str,
        capabilities: list[str],
        best_for:     list[str],
    ) -> None:
        """Register a tool. Raises TypeError if obj is not a BaseTool."""
        if not isinstance(tool, BaseTool):
            raise TypeError(
                f"ToolRegistry only accepts BaseTool subclasses, "
                f"got {type(tool).__name__}. Use AgentRegistry for agents."
            )
        self._entries[tool.name] = {
            "name":         tool.name,
            "entry_type":   "tool",
            "description":  description,
            "capabilities": capabilities,
            "best_for":     best_for,
            "obj":          tool,
        }

    def all_metadata(self) -> list[dict]:
        """Return metadata for all registered tools (no obj reference)."""
        return [{k: v for k, v in e.items() if k != "obj"}
                for e in self._entries.values()]

    def get(self, name: str) -> BaseTool:
        return self._entries[name]["obj"]

    def get_entry(self, name: str) -> dict:
        return self._entries[name]

    def __contains__(self, name: str) -> bool:
        return name in self._entries

    def __len__(self) -> int:
        return len(self._entries)
