"""SwarmEngine — the core choreography execution loop.

This is the heart of the Swarm pattern. Unlike orchestrators in other
patterns, the SwarmEngine does NOT decide who speaks next. It only:

  1. Routes each message to the agent the PREVIOUS agent chose.
  2. Tracks the conversation history.
  3. Checks termination conditions after each turn.

Termination conditions (checked in order)
-----------------------------------------
a. Consensus: the current agent signals consensus=True AND chooses
   next_agent=TERMINATE, OR two or more agents have signalled
   consensus=True across the conversation.

b. Max iterations: the hard ceiling on total turns, preventing
   infinite loops if agents never reach consensus.

The engine returns the full conversation history plus metadata
(termination reason, total iterations, consensus status).
"""


class SwarmEngine:
    """Routes messages between swarm agents until termination.

    Parameters
    ----------
    agents        : List of SwarmAgent instances in the pool.
    max_iterations: Hard limit on the number of agent turns.
    """

    def __init__(self, agents: list, max_iterations: int = 6):
        self.agent_map:     dict = {a.name: a for a in agents}
        self.max_iterations: int = max_iterations

    # ------------------------------------------------------------------
    # Main execution loop
    # ------------------------------------------------------------------

    def run(self, task: str, first_agent_name: str) -> dict:
        """Execute the swarm conversation.

        Parameters
        ----------
        task             : The task the swarm will tackle.
        first_agent_name : The agent selected by the Dispatcher to open.

        Returns
        -------
        {
            "history"            : list[dict]  — all swarm messages in order
            "termination_reason" : str         — "consensus" | "max_iterations"
            "consensus_reached"  : bool
            "total_iterations"   : int
        }
        """
        if first_agent_name not in self.agent_map:
            first_agent_name = next(iter(self.agent_map))

        history:          list[dict] = []
        consensus_votes:  int        = 0
        termination_reason: str      = "max_iterations"
        agent_names: list[str]       = list(self.agent_map.keys())
        current_agent                = self.agent_map[first_agent_name]

        for iteration in range(1, self.max_iterations + 1):

            # ── Agent takes its turn ───────────────────────────────────
            response = current_agent.swarm_respond(
                task=task,
                history=history,
                available_agents=agent_names,
                iteration=iteration,
            )

            # ── Record the message ─────────────────────────────────────
            history.append({
                "iteration":  iteration,
                "from_agent": current_agent.name,
                "content":    response["contribution"],
                "next_agent": response["next_agent"],
                "consensus":  response["consensus"],
                "reasoning":  response["reasoning"],
            })

            # ── Tally consensus votes ──────────────────────────────────
            if response["consensus"]:
                consensus_votes += 1

            next_name = response["next_agent"]

            # ── Check termination ──────────────────────────────────────
            # Condition A: explicit TERMINATE + consensus signal
            if next_name == "TERMINATE" and response["consensus"]:
                termination_reason = "consensus"
                break

            # Condition B: majority consensus (2+ agents agree we're done)
            if consensus_votes >= 2:
                termination_reason = "consensus"
                break

            # Condition C: unknown next agent
            if next_name not in self.agent_map:
                termination_reason = "max_iterations"
                break

            # ── Route to next agent ────────────────────────────────────
            current_agent = self.agent_map[next_name]

        return {
            "history":             history,
            "termination_reason":  termination_reason,
            "consensus_reached":   termination_reason == "consensus",
            "total_iterations":    len(history),
        }
