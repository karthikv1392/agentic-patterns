"""Adapter — Registry & Adapter pattern.

The Problem
-----------
Agents (BaseAgent) and tools (BaseTool) have different interfaces:
  • Agent  : respond(task: str) -> str          needs a natural-language prompt
  • Tool   : run(task: str) -> str              needs a task string (may differ in semantics)

The orchestrator should not need to know which type it is talking to.

The Solution — Adapter
-----------------------
`Adapter.invoke(sub_task, context)` is a single, uniform call that works
for any registered entry. Internally it delegates to the right method
and normalises the output into the same dict shape regardless of type.

This is the Adapter Design Pattern applied to a multi-agent system:
  Orchestrator → Adapter.invoke() → [AgentAdapter | ToolAdapter] → Agent/Tool

Adding new agent types or tool types only requires a new internal branch
inside `_invoke_agent` or `_invoke_tool` — the orchestrator is untouched.
"""

from shared.base_agent import BaseAgent
from shared.base_tool  import BaseTool
from shared.llm        import generate_response


class Adapter:
    """Uniform invocation wrapper for any registered agent or tool.

    Parameters
    ----------
    name       : registry name of the wrapped entry
    entry_type : "agent" | "tool"
    obj        : the actual BaseAgent or BaseTool instance
    metadata   : registry metadata dict (description, capabilities, best_for)
    """

    def __init__(self, name: str, entry_type: str, obj, metadata: dict):
        self.name       = name
        self.entry_type = entry_type
        self._obj       = obj
        self.metadata   = metadata

    # ------------------------------------------------------------------
    # Uniform interface
    # ------------------------------------------------------------------

    def invoke(self, sub_task: str, context: str = "") -> dict:
        """Invoke the wrapped agent or tool with a normalised interface.

        Parameters
        ----------
        sub_task : the specific sub-task assigned to this entry
        context  : accumulated output from prior steps (shared memory)

        Returns
        -------
        {
            "name"       : str  — registry name
            "entry_type" : str  — "agent" | "tool"
            "sub_task"   : str  — what was asked
            "output"     : str  — the result
        }
        """
        if self.entry_type == "agent":
            output = self._invoke_agent(sub_task, context)
        else:
            output = self._invoke_tool(sub_task, context)

        return {
            "name":       self.name,
            "entry_type": self.entry_type,
            "sub_task":   sub_task,
            "output":     output,
        }

    # ------------------------------------------------------------------
    # Type-specific adapters
    # ------------------------------------------------------------------

    def _invoke_agent(self, sub_task: str, context: str) -> str:
        """Adapt orchestrator call → BaseAgent.respond()."""
        assert isinstance(self._obj, BaseAgent)

        # Inject accumulated context from prior steps as a preamble
        if context.strip():
            full_task = (
                f"Context from prior steps in this pipeline:\n"
                f"{context}\n\n"
                f"Your assigned task (focus on this):\n{sub_task}"
            )
        else:
            full_task = sub_task

        return self._obj.respond(full_task)

    def _invoke_tool(self, sub_task: str, context: str) -> str:
        """Adapt orchestrator call → BaseTool.run()."""
        assert isinstance(self._obj, BaseTool)

        # For tools, embed context directly in the task string if present
        if context.strip():
            full_task = (
                f"Context:\n{context}\n\n"
                f"Tool task:\n{sub_task}"
            )
        else:
            full_task = sub_task

        return self._obj.run(full_task)

    def __repr__(self) -> str:
        return f"Adapter(name={self.name!r}, type={self.entry_type!r})"


# ---------------------------------------------------------------------------
# Factory — build an Adapter from a registry entry dict
# ---------------------------------------------------------------------------

def adapter_from_entry(entry: dict) -> Adapter:
    """Convenience factory: create an Adapter from a registry entry dict."""
    return Adapter(
        name       = entry["name"],
        entry_type = entry["entry_type"],
        obj        = entry["obj"],
        metadata   = {k: v for k, v in entry.items() if k not in ("obj",)},
    )
