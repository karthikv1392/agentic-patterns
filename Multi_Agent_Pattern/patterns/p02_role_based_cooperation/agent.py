"""Role-based Cooperation — orchestrator entry point.

Flow
----
1. The orchestrator LLM divides the user task into per-role sub-tasks.
2. Agents execute in sequence: PM → Architect → Developer → QA.
3. Each agent receives its sub-task PLUS the accumulated shared memory
   (all prior agent outputs), enabling genuine handoffs.
4. A final synthesis LLM call weaves all contributions into one document.

Shared Memory
-------------
A plain dict grows as each agent completes its step:
    {}
    → {"Product Manager": "...PM output..."}
    → {"Product Manager": "...", "System Architect": "..."}
    → ... and so on.

This is "message passing through shared state" — the simplest coordination
primitive, easy to swap out for a vector store or message queue later.
"""

from patterns.p02_role_based_cooperation.agent_product_manager import ProductManagerAgent
from patterns.p02_role_based_cooperation.agent_architect       import ArchitectAgent
from patterns.p02_role_based_cooperation.agent_developer       import DeveloperAgent
from patterns.p02_role_based_cooperation.agent_qa_engineer     import QAEngineerAgent
from patterns.p02_role_based_cooperation.orchestrator          import divide_task, synthesise

# Ordered pipeline — the sequence matters: each agent builds on the previous
PIPELINE = [
    ProductManagerAgent(),
    ArchitectAgent(),
    DeveloperAgent(),
    QAEngineerAgent(),
]


def run(task: str) -> dict:
    """Run the full role-based cooperation pipeline.

    Parameters
    ----------
    task : the user's high-level task or problem statement

    Returns
    -------
    {
        "task"          : str         — original task
        "assignments"   : dict        — per-role sub-tasks from orchestrator
        "step_outputs"  : list[dict]  — each agent's result in pipeline order
        "shared_memory" : dict        — final accumulated agent outputs
        "final_output"  : str         — synthesised document
    }
    """
    # Step 1 — orchestrator divides the task
    assignments = divide_task(task)

    # Step 2 — sequential execution with shared memory handoffs
    shared_memory: dict[str, str] = {}
    step_outputs: list[dict] = []

    for agent in PIPELINE:
        sub_task = assignments.get(agent.role, f"Apply your {agent.role} expertise to: {task}")
        result   = agent.execute(sub_task, prior_outputs=shared_memory)
        step_outputs.append(result)
        shared_memory[agent.name] = result["output"]   # handoff

    # Step 3 — synthesise all contributions
    final_output = synthesise(task, shared_memory)

    return {
        "task":          task,
        "assignments":   assignments,
        "step_outputs":  step_outputs,
        "shared_memory": shared_memory,
        "final_output":  final_output,
    }
