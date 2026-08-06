"""Sub-Agent Spawning — entry point.

Pattern flow
------------
1. SpawnerAgent  — one LLM call analyzes the task and generates N sub-agent
                   specifications (name, persona, task) entirely at runtime.
2. SubAgent spawn — N SubAgent instances are created dynamically from the specs.
                    No SubAgent class is pre-defined; they emerge from the LLM output.
3. Parallel exec  — All sub-agents execute concurrently via ThreadPoolExecutor.
                    Each agent only holds context relevant to its scoped task.
4. Synthesizer   — Integrates all outputs using the Spawner's synthesis_hint.

Key distinction from p05 (Parallel Fan-Out)
--------------------------------------------
p05: Pre-defined agents (Researcher, Analyst, Strategist, Critic) with fixed roles.
p10: Agents are invented at runtime — their names, personas, and tasks are LLM output.
     The number of agents is also decided by the LLM based on task complexity.
"""

import concurrent.futures
import time

from patterns.p10_subagent_spawning.spawner     import SpawnerAgent
from patterns.p10_subagent_spawning.subagent    import SubAgent
from patterns.p10_subagent_spawning.synthesizer import synthesize

SPAWNER = SpawnerAgent()


def run(
    task: str,
    domain: str = "Code Migration",
    max_subagents: int = 5,
) -> dict:
    """Run the full Sub-Agent Spawning pipeline.

    Parameters
    ----------
    task          : The complex task to execute.
    domain        : Task domain — shapes how the Spawner decomposes.
                    One of: "Code Migration", "Code Transformation",
                            "Document Analysis", "System Design"
    max_subagents : Upper bound on spawned agents (2-6).

    Returns
    -------
    {
        "task"               : str,
        "domain"             : str,
        "max_subagents"      : int,
        "spawn_plan"         : dict,   — full Spawner output (strategy, rationale, specs)
        "subagents_spawned"  : int,
        "results"            : list,   — per-sub-agent execution dicts
        "synthesis"          : dict,   — Synthesizer output
        "final_output"       : str,
        "wall_time_s"        : float,
        "max_agent_latency_s": float,
        "total_seq_latency_s": float,
        "parallel_speedup"   : float,  — total_seq / wall_time (efficiency gain)
    }
    """
    # ── Step 1: Spawner analyzes task → generates sub-agent specs ─────────
    spawn_plan = SPAWNER.analyze_and_spawn(task, domain, max_subagents)
    specs      = spawn_plan["subagent_specs"]

    # ── Step 2: Instantiate SubAgent objects at runtime ───────────────────
    subagents = [SubAgent(spec) for spec in specs]

    # ── Step 3: Execute all sub-agents in parallel ────────────────────────
    wall_start = time.time()
    results: list[dict] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(subagents)) as pool:
        futures = {pool.submit(agent.execute_task): agent for agent in subagents}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    wall_elapsed = round(time.time() - wall_start, 2)

    # Sort by agent_id for stable display order
    results.sort(key=lambda r: r["agent_id"])

    # ── Step 4: Synthesize ────────────────────────────────────────────────
    synthesis = synthesize(
        task=task,
        domain=domain,
        strategy=spawn_plan.get("strategy", ""),
        results=results,
        synthesis_hint=spawn_plan.get("synthesis_hint", "Integrate all outputs."),
    )

    max_latency = max(r["latency_s"] for r in results) if results else 0.0
    seq_latency = sum(r["latency_s"] for r in results)
    speedup     = round(seq_latency / wall_elapsed, 2) if wall_elapsed > 0 else 1.0

    return {
        "task":                task,
        "domain":              domain,
        "max_subagents":       max_subagents,
        "spawn_plan":          spawn_plan,
        "subagents_spawned":   len(subagents),
        "results":             results,
        "synthesis":           synthesis,
        "final_output":        synthesis["final_output"],
        "wall_time_s":         wall_elapsed,
        "max_agent_latency_s": round(max_latency, 2),
        "total_seq_latency_s": round(seq_latency, 2),
        "parallel_speedup":    speedup,
    }
