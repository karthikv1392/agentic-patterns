"""Swarm (Choreography) — entry point.

Choreography vs Orchestration
------------------------------
Every other pattern in this repo uses ORCHESTRATION: a central coordinator
(Root Agent, Orchestrator, Coordinator) decides who does what and when.

The Swarm uses CHOREOGRAPHY: each agent decides who to engage next.
The Dispatcher does not control the flow — it only starts it and
synthesises the end result. In between, agents communicate peer-to-peer.

Swarm roster
------------
  Dispatcher  — entry/exit only; selects first agent; synthesises final answer
  Ideator     — generates bold, original ideas and proposals
  Critic      — stress-tests ideas; finds flaws and blind spots
  Refiner     — integrates critiques; produces polished proposals
  Validator   — quality gate; signals consensus when the bar is met

Termination
-----------
  Consensus    : Validator (or 2+ agents) signals consensus=True
  Max iterations: hard ceiling to prevent infinite loops
"""

from patterns.p07_swarm.dispatcher      import DispatcherAgent
from patterns.p07_swarm.agent_ideator   import IdeatorAgent
from patterns.p07_swarm.agent_critic    import CriticAgent
from patterns.p07_swarm.agent_refiner   import RefinerAgent
from patterns.p07_swarm.agent_validator import ValidatorAgent
from patterns.p07_swarm.swarm           import SwarmEngine

# Module-level singletons — used by app.py for the sidebar roster
DISPATCHER   = DispatcherAgent()
SWARM_AGENTS = [
    IdeatorAgent(),
    CriticAgent(),
    RefinerAgent(),
    ValidatorAgent(),
]


def run(task: str, max_iterations: int = 6) -> dict:
    """Execute the full Swarm pipeline.

    Flow
    ----
    1. Dispatcher.select_first()  — picks the opening agent
    2. SwarmEngine.run()          — choreographed peer-to-peer conversation
    3. Dispatcher.synthesise()    — integrates the full conversation

    Parameters
    ----------
    task           : The task for the swarm to tackle.
    max_iterations : Hard ceiling on agent turns (3-8, default 6).

    Returns
    -------
    {
        "task"               : str
        "dispatch"           : dict   — first agent selection + reasoning
        "swarm_history"      : list   — every swarm message in order
        "termination_reason" : str    — "consensus" | "max_iterations"
        "consensus_reached"  : bool
        "total_iterations"   : int
        "final_answer"       : str    — Dispatcher's synthesis of all outputs
    }
    """
    agent_names = [a.name for a in SWARM_AGENTS]

    # ── Step 1: Dispatcher selects first agent ─────────────────────────
    dispatch = DISPATCHER.select_first(task, agent_names)
    first_agent_name = dispatch["first_agent"]

    # ── Step 2: Swarm executes via peer-to-peer choreography ───────────
    engine = SwarmEngine(agents=SWARM_AGENTS, max_iterations=max_iterations)
    swarm_result = engine.run(task, first_agent_name)

    # ── Step 3: Dispatcher synthesises the collective output ───────────
    final_answer = DISPATCHER.synthesise(task, swarm_result["history"])

    return {
        "task":               task,
        "dispatch":           dispatch,
        "swarm_history":      swarm_result["history"],
        "termination_reason": swarm_result["termination_reason"],
        "consensus_reached":  swarm_result["consensus_reached"],
        "total_iterations":   swarm_result["total_iterations"],
        "final_answer":       final_answer,
    }
