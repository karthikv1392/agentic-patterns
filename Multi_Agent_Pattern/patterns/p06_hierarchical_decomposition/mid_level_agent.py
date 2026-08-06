"""Mid-Level Agent — Level 1 in the 3-tier hierarchy.

Mid-level agents are the domain coordinators. Each one:
  1. Receives a high-level domain task from the Root Agent.
  2. Uses an LLM call to further decompose it into precise worker sub-tasks.
  3. Delegates each sub-task to a Worker Agent with a specific tool.
  4. Reads all worker outputs from shared HierarchyMemory.
  5. Synthesises a cohesive domain-level report from those outputs.

There is one Mid-level Agent per domain (e.g. "Background & Context Lead",
"Current State Lead", "Future Implications Lead"). They do not communicate
with each other — their outputs are collected by the Root Agent.

Design
------
- Decomposition (step 2) is an LLM call scoped to the domain.
- Each worker gets a distinct tool from TOOL_POOL (cycling if more workers
  than tools exist), ensuring diverse research perspectives within the domain.
- Synthesis (step 5) is an LLM call that reads memory and integrates findings.
"""

import json
import re

from shared.base_agent import BaseAgent
from shared.llm import generate_response

from patterns.p06_hierarchical_decomposition.memory     import HierarchyMemory
from patterns.p06_hierarchical_decomposition.tools      import TOOL_POOL
from patterns.p06_hierarchical_decomposition.worker_agent import WorkerAgent


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


class MidLevelAgent(BaseAgent):
    """Domain coordinator: decomposes, delegates to workers, and synthesises.

    Parameters
    ----------
    name         : Display name, e.g. "Background & Context Lead"
    domain       : Short domain label, e.g. "Background & Context"
    domain_index : 0-based position in the domain list (for colour-coding)
    num_workers  : How many worker agents to spawn under this domain (2-3)
    """

    def __init__(
        self,
        name: str,
        domain: str,
        domain_index: int = 0,
        num_workers: int = 2,
    ):
        super().__init__(name=name, model_name="gemma4")
        self._domain       = domain
        self.domain_index  = domain_index
        self.num_workers   = num_workers

        # Create workers, each assigned a distinct tool from the pool
        self.workers: list[WorkerAgent] = [
            WorkerAgent(
                name=f"{domain} · Worker {i + 1}",
                tool=TOOL_POOL[i % len(TOOL_POOL)],
                worker_index=i + 1,
            )
            for i in range(num_workers)
        ]

    @property
    def persona(self) -> str:
        return (
            f"You are the senior domain lead for '{self._domain}'. "
            "You coordinate a small team of specialist workers, "
            "decompose your domain into focused research sub-tasks, "
            "and synthesise your team's findings into a precise domain report."
        )

    @property
    def role(self) -> str:
        return self._domain

    @property
    def tier(self) -> str:
        return "mid_level"

    # ------------------------------------------------------------------
    # Step 2 — Decompose domain task into worker sub-tasks
    # ------------------------------------------------------------------

    def _decompose_domain(self, domain_task: str) -> list[dict]:
        """LLM call: break domain task into one focused sub-task per worker."""
        tool_lines = "\n".join(
            f"  Worker {i + 1} — uses '{w.tool.name}': {w.tool.description}"
            for i, w in enumerate(self.workers)
        )
        prompt = (
            f"You are coordinating the '{self._domain}' research domain.\n\n"
            f"Domain task assigned by your supervisor:\n{domain_task}\n\n"
            f"You have {self.num_workers} workers with these tools:\n{tool_lines}\n\n"
            f"Decompose the domain task into exactly {self.num_workers} sub-tasks — "
            "one per worker. Each sub-task must:\n"
            "  • Be self-contained and directly executable by the assigned tool.\n"
            "  • Cover a distinct, non-overlapping dimension of the domain task.\n"
            "  • Be phrased as a specific research directive (1-2 sentences).\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "sub_tasks": [\n'
            '    {"worker_index": 1, "sub_task": "specific directive for worker 1"},\n'
            "    ...\n"
            "  ]\n"
            "}"
        )
        raw = generate_response(prompt, model_name=self.model_name)
        data = _extract_json(raw)
        sub_tasks = data.get("sub_tasks", [])

        if len(sub_tasks) >= self.num_workers:
            return sub_tasks

        # Fallback: assign domain task with tool-specific framing
        return [
            {
                "worker_index": i + 1,
                "sub_task": (
                    f"{domain_task} — focus specifically on the "
                    f"{w.tool.name.lower()} perspective."
                ),
            }
            for i, w in enumerate(self.workers)
        ]

    # ------------------------------------------------------------------
    # Step 5 — Synthesise worker outputs into a domain report
    # ------------------------------------------------------------------

    def _synthesise_domain(
        self,
        domain_task: str,
        worker_outputs: dict[str, str],
    ) -> str:
        """LLM call: integrate all worker outputs into a domain report."""
        context = "\n\n".join(
            f"--- {worker_name} ---\n{output}"
            for worker_name, output in worker_outputs.items()
        )
        prompt = (
            f"{self.persona}\n\n"
            f"Your domain task:\n{domain_task}\n\n"
            "Your workers have completed their sub-tasks. Their findings from memory:\n\n"
            f"{context}\n\n"
            "Synthesise these findings into a comprehensive, well-structured domain report. "
            "Integrate complementary insights, highlight the most important findings, "
            "eliminate redundancy, and present a coherent picture of your domain. "
            "Use markdown formatting with clear sections. 400-600 words."
        )
        return generate_response(prompt, model_name=self.model_name)

    # ------------------------------------------------------------------
    # Public API — full mid-level workflow
    # ------------------------------------------------------------------

    def execute(self, domain_task: str, memory: HierarchyMemory) -> dict:
        """Run the full mid-level pipeline for this domain.

        Parameters
        ----------
        domain_task : The specific research directive from the Root Agent.
        memory      : Shared HierarchyMemory — workers write here, we read from it.

        Returns
        -------
        {
            "agent_name"     : str
            "domain"         : str
            "domain_index"   : int
            "model"          : str
            "domain_task"    : str
            "sub_tasks"      : list[dict]  — decomposition output
            "worker_outputs" : list[dict]  — each worker's execution result
            "synthesis"      : str         — domain-level summary
        }
        """
        # ── Step 2: Decompose domain into worker sub-tasks ─────────────
        sub_tasks = self._decompose_domain(domain_task)

        # ── Step 3: Execute each worker with its sub-task ──────────────
        worker_outputs: list[dict] = []
        for i, worker in enumerate(self.workers):
            sub_task_text = (
                sub_tasks[i]["sub_task"]
                if i < len(sub_tasks)
                else f"{domain_task} ({worker.tool.name} perspective)"
            )
            result = worker.execute_task(sub_task_text, self._domain, memory)
            worker_outputs.append(result)

        # ── Step 4: Read from memory → Step 5: Synthesise ─────────────
        domain_memory = memory.read_domain(self._domain)
        synthesis     = self._synthesise_domain(domain_task, domain_memory)

        return {
            "agent_name":     self.name,
            "domain":         self._domain,
            "domain_index":   self.domain_index,
            "model":          self.model_name,
            "domain_task":    domain_task,
            "sub_tasks":      sub_tasks,
            "worker_outputs": worker_outputs,
            "synthesis":      synthesis,
        }
