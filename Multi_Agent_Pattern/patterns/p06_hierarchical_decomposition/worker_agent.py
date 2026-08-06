"""Worker Agent — Level 2 (leaf) in the 3-tier hierarchy.

Workers are the execution units of the hierarchy. Each worker:
  - Receives a precise, atomic sub-task from its mid-level supervisor.
  - Uses ONE assigned specialist tool to carry out that sub-task.
  - Writes its output to the shared HierarchyMemory under its domain key.

Workers do NOT delegate further — they are the deepest reasoning layer.
Their outputs are later read by the mid-level agent for domain synthesis.

Tool assignment
---------------
Workers are created with a specific tool (WebResearchTool, FactExtractorTool,
or DataAnalystTool), giving each worker a distinct capability even when they
tackle related sub-tasks in the same domain.
"""

from shared.base_agent import BaseAgent
from patterns.p06_hierarchical_decomposition.memory import HierarchyMemory


class WorkerAgent(BaseAgent):
    """Leaf-level agent that executes one atomic sub-task using a specialist tool.

    Parameters
    ----------
    name         : Display name, e.g. "Background & Context Worker 1"
    tool         : One of the tools from tools.py (WebResearchTool, etc.)
    worker_index : 1-based position within the domain's worker pool
    """

    def __init__(self, name: str, tool, worker_index: int = 1):
        super().__init__(name=name, model_name="gemma4")
        self.tool = tool
        self.worker_index = worker_index

    @property
    def persona(self) -> str:
        return (
            f"You are a focused specialist worker using the '{self.tool.name}' instrument. "
            "You execute precise, well-scoped sub-tasks with accuracy and depth, "
            "then document your findings clearly for your supervising agent to synthesise."
        )

    @property
    def tier(self) -> str:
        return "worker"

    def execute_task(
        self,
        sub_task: str,
        domain: str,
        memory: HierarchyMemory,
    ) -> dict:
        """Execute the assigned sub-task, write output to shared memory.

        Parameters
        ----------
        sub_task : The precise task assigned by the mid-level agent.
        domain   : The domain key used for memory partitioning.
        memory   : Shared HierarchyMemory — this worker writes its output here.

        Returns
        -------
        {
            "worker_name" : str  — display name of this worker
            "tool_name"   : str  — tool used
            "tool_icon"   : str  — emoji icon for the tool
            "sub_task"    : str  — the task that was executed
            "domain"      : str  — the domain this worker belongs to
            "output"      : str  — the tool's output (written to memory)
        }
        """
        output = self.tool.run(sub_task)
        memory.write(domain, self.name, output)
        return {
            "worker_name": self.name,
            "tool_name":   self.tool.name,
            "tool_icon":   self.tool.icon,
            "sub_task":    sub_task,
            "domain":      domain,
            "output":      output,
        }
