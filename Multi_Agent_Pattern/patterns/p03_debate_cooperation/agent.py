"""Debate-based Cooperation — entry point.

Flow
----
1. All debater agents receive the same topic and give opening statements (round 0).
2. For rounds 1..K each agent reads the full prior transcript and produces
   a rebuttal — addressing specific arguments, defending or revising their stance.
3. After all rounds the Judge reads the complete transcript and delivers a
   structured verdict: agreements, disagreements, position shifts, final answer.

The three debaters have deliberately distinct temperaments:
  🔍 Skeptic    — challenges claims, demands evidence, resists premature consensus
  ⚙️  Pragmatist — focuses on real-world feasibility and workable compromise
  🚀 Visionary  — pushes for ambitious, first-principles thinking
"""

from patterns.p03_debate_cooperation.agent_skeptic    import SkepticAgent
from patterns.p03_debate_cooperation.agent_pragmatist import PragmatistAgent
from patterns.p03_debate_cooperation.agent_visionary  import VisionaryAgent
from patterns.p03_debate_cooperation.agent_judge      import JudgeAgent
from patterns.p03_debate_cooperation.debate           import run_debate

# The panel of debaters — order affects who goes first each round
DEBATERS = [
    SkepticAgent(),
    PragmatistAgent(),
    VisionaryAgent(),
]

JUDGE = JudgeAgent()


def run(task: str, num_rounds: int = 2) -> dict:
    """Run the full debate-cooperation pipeline.

    Parameters
    ----------
    task       : the question / problem to debate
    num_rounds : how many rounds (1 = opening statements only,
                 2 = one rebuttal, 3 = two rebuttals)

    Returns
    -------
    {
        "task"           : str        — original topic
        "num_rounds"     : int        — rounds run
        "debate_history" : list[dict] — full round-by-round transcript
        "verdict"        : dict       — judge's structured ruling
    }
    """
    debate_history = run_debate(DEBATERS, task, num_rounds)
    verdict        = JUDGE.adjudicate(task, debate_history)

    return {
        "task":           task,
        "num_rounds":     num_rounds,
        "debate_history": debate_history,
        "verdict":        verdict,
    }
