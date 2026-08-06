"""Debate engine — runs K rounds of multi-agent structured debate.

Each round every debater reads the full transcript of all previous rounds
(excluding their own prior turns, which are shown separately), then produces
a new response. This creates genuine back-and-forth: agents reference each
other by name, rebut specific claims, and may shift their positions.

Round structure
---------------
Round 0  — Opening statements  : each agent states their initial position
           independently (no prior transcript exists).
Round 1+ — Rebuttal rounds     : each agent reads all prior responses from
           all agents and must address at least one argument explicitly.

The engine returns a debate_history list that is passed to the Judge.
"""


def run_debate(agents: list, task: str, num_rounds: int) -> list[dict]:
    """Run num_rounds of structured debate between all agents.

    Parameters
    ----------
    agents     : list of BaseAgent subclasses (the debaters)
    task       : the question / problem being debated
    num_rounds : total rounds (1 = opening statements only, 2+ = with rebuttals)

    Returns
    -------
    debate_history : list of round dicts
        [
            {
                "round": 0,
                "label": "Opening Statements",
                "responses": [{"agent_name", "model", "round", "response"}, ...]
            },
            {
                "round": 1,
                "label": "Rebuttal Round 1",
                "responses": [...]
            },
            ...
        ]
    """
    debate_history: list[dict] = []

    for round_num in range(num_rounds):
        round_responses = []
        for agent in agents:
            response = agent.debate(task, round_num, debate_history)
            round_responses.append(response)

        label = "Opening Statements" if round_num == 0 else f"Rebuttal Round {round_num}"
        debate_history.append({
            "round":     round_num,
            "label":     label,
            "responses": round_responses,
        })

    return debate_history
