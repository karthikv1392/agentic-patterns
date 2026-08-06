"""Base tool — abstract class that all registered tools extend.

Tools vs Agents
---------------
Agents (BaseAgent) hold a persona and generate free-form LLM responses.
Tools (BaseTool) are DETERMINISTIC helpers — they must NOT call any LLM.
They implement narrow, well-defined functions using standard Python libraries
(regex, math, collections, etc.) so the same input always produces the same
output. This is the key distinction: agents reason, tools compute.

Both can be registered in the Registry and invoked through an Adapter,
which is exactly the point: the orchestrator doesn't need to know whether
it's talking to an agent or a tool — the adapter normalises the interface.

Subclass template
-----------------
class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "My Tool"

    @property
    def description(self) -> str:
        return "Does X given Y."

    @property
    def capabilities(self) -> list[str]:
        return ["keyword1", "keyword2"]

    def run(self, task: str) -> str:
        # implement the tool logic here
        ...
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base for all registered tools."""

    # ------------------------------------------------------------------
    # Identity — subclasses must implement all three properties
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique display name for the registry."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """One-sentence description of what this tool does."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """Keyword tags used by the registry to match tool to task.

        Examples: ["summarise", "condense", "tldr"]
        """
        ...

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    @abstractmethod
    def run(self, task: str) -> str:
        """Execute the tool given a natural-language task description.

        Parameters
        ----------
        task : what the orchestrator needs this tool to do (full sentence)

        Returns
        -------
        str : the tool's output (plain text or markdown)
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
