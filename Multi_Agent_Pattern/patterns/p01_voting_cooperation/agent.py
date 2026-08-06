"""Voting-based Cooperation — orchestrator.

Flow
----
1. All N agents receive the same task.
2. Each agent independently produces a response (its "vote").
3. The aggregator collects all votes and applies the chosen strategy
   (majority | weighted | llm) to produce the final decision.

Returns a structured dict so the Streamlit UI can display every stage.
"""

from patterns.p01_voting_cooperation.agent_conservative import ConservativeAgent
from patterns.p01_voting_cooperation.agent_creative     import CreativeAgent
from patterns.p01_voting_cooperation.agent_analytical   import AnalyticalAgent
from patterns.p01_voting_cooperation.aggregator         import aggregate

# The voting panel — add or swap agents here to change ensemble composition
AGENTS = [
    ConservativeAgent(),
    CreativeAgent(),
    AnalyticalAgent(),
]


def run(task: str, aggregation_mode: str = "llm") -> dict:
    """Run the full voting-cooperation pipeline.

    Parameters
    ----------
    task             : The question or problem every agent will answer.
    aggregation_mode : "majority" | "weighted" | "llm"

    Returns
    -------
    {
        "task"             : str            — original task
        "aggregation_mode" : str            — mode used
        "votes"            : list[dict]     — each agent's raw vote
        "aggregation"      : dict           — aggregator output
    }
    """
    # Step 1 — collect votes from all agents
    votes = [agent.vote(task) for agent in AGENTS]

    # Step 2 — aggregate
    aggregation = aggregate(votes, mode=aggregation_mode)

    return {
        "task":             task,
        "aggregation_mode": aggregation_mode,
        "votes":            votes,
        "aggregation":      aggregation,
    }
