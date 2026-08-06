"""Hierarchical Task Decomposition — orchestrator.

Three-tier hierarchy
--------------------
Level 0 — Root Agent (1)
    Receives the complex task. Decomposes into N high-level domain areas.
    After all domains are done, synthesises a final cross-domain report.

Level 1 — Mid-level Agents (N)
    One per domain. Each decomposes its domain into M worker sub-tasks,
    delegates to workers, reads their memory outputs, and produces a
    domain synthesis.

Level 2 — Worker Agents (N × M)
    Leaf agents. Each executes ONE precise sub-task using ONE specialist
    tool (Web Research, Fact Extractor, or Data Analyst). Writes its
    output to shared HierarchyMemory.

Information flow
----------------
    Root decomposes → [delegates to mid-levels]
    Each mid-level decomposes → [delegates to workers]
    Each worker executes tool → writes to memory
    Mid-level reads memory → synthesises domain report
    Root collects domain reports → synthesises final answer

LLM call budget
---------------
    1 (root decompose)
  + N (mid-level decompose)
  + N × M (worker tool calls)
  + N (mid-level synthesise)
  + 1 (root synthesise)
  = 2 + 2N + N×M

For N=3, M=2: 2 + 6 + 6 = 14 calls.
"""

from patterns.p06_hierarchical_decomposition.memory       import HierarchyMemory
from patterns.p06_hierarchical_decomposition.root_agent   import RootAgent
from patterns.p06_hierarchical_decomposition.mid_level_agent import MidLevelAgent

ROOT_AGENT = RootAgent()


def run(
    task: str,
    num_domains: int = 3,
    workers_per_domain: int = 2,
) -> dict:
    """Execute the full Hierarchical Task Decomposition pipeline.

    Parameters
    ----------
    task               : Complex research task from the user.
    num_domains        : Number of Level-1 domains / mid-level agents (2-3).
    workers_per_domain : Number of Level-2 workers per domain (2-3).

    Returns
    -------
    {
        "task"               : str
        "decomposition"      : dict         — root agent's domain decomposition
        "mid_level_results"  : list[dict]   — each domain's full result tree
        "final_output"       : str          — root agent's final synthesis
        "memory_snapshot"    : dict         — full HierarchyMemory at completion
        "total_llm_calls"    : int          — estimated LLM call count
    }
    """
    memory = HierarchyMemory()

    # ── Level 0: Root Agent decomposes ────────────────────────────────────
    decomposition = ROOT_AGENT.decompose(task, num_domains=num_domains)
    domains = decomposition.get("domains", [])[:num_domains]

    # Guard: ensure we have enough domain entries
    while len(domains) < num_domains:
        idx = len(domains) + 1
        domains.append({
            "index":       idx,
            "name":        f"Domain {idx}",
            "description": f"Research dimension {idx} of the task.",
            "task":        task,
        })

    # ── Level 1 → Level 2: Mid-level agents delegate to workers ───────────
    mid_level_results: list[dict] = []

    for domain in domains:
        mid_agent = MidLevelAgent(
            name=f"{domain['name']} Lead",
            domain=domain["name"],
            domain_index=domain["index"] - 1,   # 0-based for colour coding
            num_workers=workers_per_domain,
        )
        result = mid_agent.execute(domain["task"], memory)
        mid_level_results.append(result)

    # ── Level 0 return: Root Agent synthesises all domain outputs ──────────
    domain_syntheses: dict[str, str] = {
        r["domain"]: r["synthesis"]
        for r in mid_level_results
    }
    final_output = ROOT_AGENT.synthesise(task, domain_syntheses)

    total_llm_calls = (
        1                                          # root decompose
        + num_domains                              # mid-level decompose
        + (num_domains * workers_per_domain)       # workers
        + num_domains                              # mid-level synthesise
        + 1                                        # root synthesise
    )

    return {
        "task":              task,
        "decomposition":     decomposition,
        "mid_level_results": mid_level_results,
        "final_output":      final_output,
        "memory_snapshot":   memory.read_all(),
        "total_llm_calls":   total_llm_calls,
    }
