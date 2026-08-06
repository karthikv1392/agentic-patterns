"""Parallel / Fan-Out — orchestrator.

Flow
----
1. Initiator  — one LLM call decomposes the task into N independent sub-tasks.
2. Fan-out    — N specialist agents execute *concurrently* via ThreadPoolExecutor.
               Each agent has a different persona (and can use a different model
               or data source), maximising parallel diversity.
3. Synthesiser — collects all outputs and aggregates using the chosen strategy
               (merge | summarise | vote).

Key property
------------
Total wall-clock latency ≈ max(sub-task latencies), not their sum.
This is the core latency advantage of the Parallel/Fan-Out pattern.
"""

import concurrent.futures
import time

from patterns.p05_parallel_fanout.initiator       import decompose
from patterns.p05_parallel_fanout.agent_researcher import ResearcherAgent
from patterns.p05_parallel_fanout.agent_analyst    import AnalystAgent
from patterns.p05_parallel_fanout.agent_strategist import StrategistAgent
from patterns.p05_parallel_fanout.agent_critic     import CriticAgent
from patterns.p05_parallel_fanout.synthesiser      import synthesise

# Ordered specialist pool — sub-tasks are assigned in this order, cycling if needed
SPECIALIST_AGENTS = [
    ResearcherAgent(),
    AnalystAgent(),
    StrategistAgent(),
    CriticAgent(),
]


def _execute_agent(agent, sub_task: dict) -> dict:
    """Run one specialist on its assigned sub-task and record latency."""
    full_prompt = f"{sub_task['title']}\n\n{sub_task['description']}"
    start = time.time()
    output = agent.respond(full_prompt)
    elapsed = round(time.time() - start, 2)
    return {
        "agent_name":          agent.name,
        "model":               agent.model_name,
        "sub_task_index":      sub_task["index"],
        "sub_task_title":      sub_task["title"],
        "sub_task_description": sub_task["description"],
        "focus":               sub_task.get("focus", "general"),
        "output":              output,
        "latency_s":           elapsed,
    }


def run(task: str, num_subtasks: int = 3, synthesis_mode: str = "merge") -> dict:
    """Execute the full Parallel/Fan-Out pipeline.

    Parameters
    ----------
    task           : The complex task to fan out.
    num_subtasks   : Number of parallel branches (2-4).
    synthesis_mode : "merge" | "summarise" | "vote"

    Returns
    -------
    {
        "task"                       : str
        "decomposition"              : dict   — initiator output
        "sub_tasks"                  : list   — sub-task specs
        "results"                    : list   — per-agent outputs
        "synthesis"                  : dict   — synthesiser output
        "synthesis_mode"             : str
        "wall_time_s"                : float  — actual elapsed time
        "max_agent_latency_s"        : float  — slowest individual agent
        "total_sequential_latency_s" : float  — sum of all latencies (counterfactual)
    }
    """
    # ── Step 1: Decompose ──────────────────────────────────────────────────
    decomp    = decompose(task, num_subtasks=num_subtasks)
    sub_tasks = decomp.get("sub_tasks", [])[:num_subtasks]

    # Ensure we have exactly num_subtasks entries
    while len(sub_tasks) < num_subtasks:
        i = len(sub_tasks) + 1
        sub_tasks.append({
            "index":       i,
            "title":       f"Sub-task {i}",
            "description": task,
            "focus":       "general",
        })

    # ── Step 2: Assign sub-tasks to specialist agents ──────────────────────
    # Distribute round-robin across the specialist pool
    assignments = [
        (SPECIALIST_AGENTS[i % len(SPECIALIST_AGENTS)], sub_task)
        for i, sub_task in enumerate(sub_tasks)
    ]

    # ── Step 3: Fan-out — execute all agents concurrently ─────────────────
    wall_start = time.time()
    results: list[dict] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_subtasks) as executor:
        future_to_idx = {
            executor.submit(_execute_agent, agent, sub_task): idx
            for idx, (agent, sub_task) in enumerate(assignments)
        }
        for future in concurrent.futures.as_completed(future_to_idx):
            results.append(future.result())

    wall_elapsed = round(time.time() - wall_start, 2)

    # Sort by sub_task_index so UI renders in order
    results.sort(key=lambda r: r["sub_task_index"])

    # ── Step 4: Synthesise ─────────────────────────────────────────────────
    synthesis = synthesise(task, results, mode=synthesis_mode)

    max_latency  = max(r["latency_s"] for r in results) if results else 0.0
    seq_latency  = sum(r["latency_s"] for r in results)

    return {
        "task":                        task,
        "decomposition":               decomp,
        "sub_tasks":                   sub_tasks,
        "results":                     results,
        "synthesis":                   synthesis,
        "synthesis_mode":              synthesis_mode,
        "wall_time_s":                 wall_elapsed,
        "max_agent_latency_s":         round(max_latency, 2),
        "total_sequential_latency_s":  round(seq_latency, 2),
    }
