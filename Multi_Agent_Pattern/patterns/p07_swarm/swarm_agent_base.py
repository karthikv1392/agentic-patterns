"""SwarmAgent — base class for all agents that participate in the swarm.

Extends BaseAgent with a single new method: swarm_respond().

Key difference from all other patterns
---------------------------------------
In orchestrated patterns (Role-based, Hierarchical, Fan-Out) a central
coordinator decides who does what and when. Swarm agents have NO orchestrator
above them — they read the live conversation, produce a contribution, and
SELF-SELECT the next peer agent to engage. This is choreography, not
orchestration.

swarm_respond() contract
------------------------
The agent receives:
  - task        : the original task
  - history     : every prior swarm message (from any agent to any agent)
  - available   : list of peer agents it can hand off to
  - iteration   : current turn number

It returns:
  {
    "contribution" : str   — the agent's actual work this turn
    "next_agent"   : str   — peer to engage next, or "TERMINATE"
    "consensus"    : bool  — does this agent believe the task is fully solved?
    "reasoning"    : str   — why this next agent was chosen
  }

The engine routes the message to next_agent and repeats until termination.
"""

import json
import re

from shared.base_agent import BaseAgent
from shared.llm import generate_response


def _extract_json(text: str) -> dict:
    """Pull the first JSON object from an LLM response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def _format_history(history: list[dict]) -> str:
    """Render the full swarm transcript for injection into prompts."""
    if not history:
        return "(No prior messages — you are the first agent in this swarm.)"
    lines = []
    for msg in history:
        from_a = msg["from_agent"]
        to_a   = msg["next_agent"]
        itr    = msg["iteration"]
        lines.append(f"── Iter {itr}: {from_a} → {to_a} ──")
        lines.append(msg["content"])
        if msg.get("consensus"):
            lines.append("[↑ Consensus signal: this agent thinks the task is done]")
        lines.append("")
    return "\n".join(lines)


class SwarmAgent(BaseAgent):
    """Base class for swarm participants.

    Subclasses must implement `persona` (as always) — the persona shapes
    HOW the agent contributes in each turn, while swarm_respond() handles
    the mechanics of structured swarm communication.
    """

    # ------------------------------------------------------------------
    # Swarm API
    # ------------------------------------------------------------------

    def swarm_respond(
        self,
        task: str,
        history: list[dict],
        available_agents: list[str],
        iteration: int,
    ) -> dict:
        """Participate in one turn of the swarm conversation.

        Reads the full conversation history, reacts to the most recent
        message, adds a unique contribution, and decides who to engage next.

        Parameters
        ----------
        task             : The original task the swarm is solving.
        history          : All prior swarm messages in order.
        available_agents : Peer agents this agent can hand off to.
        iteration        : Current turn number (1-based).

        Returns
        -------
        {
            "contribution" : str   — this agent's work / reaction
            "next_agent"   : str   — peer to pass to, or "TERMINATE"
            "consensus"    : bool  — does this agent think we're done?
            "reasoning"    : str   — rationale for the next agent choice
        }
        """
        history_text = _format_history(history)
        peers = [a for a in available_agents if a != self.name]
        last_from = history[-1]["from_agent"] if history else "nobody yet"

        prompt = (
            f"{self.persona}\n\n"
            "You are participating in a multi-agent SWARM. "
            "There is no central orchestrator — agents communicate directly "
            "with each other. You received this message from "
            f"**{last_from}** and must now contribute.\n\n"
            f"ORIGINAL TASK:\n{task}\n\n"
            "SWARM CONVERSATION SO FAR:\n"
            f"{history_text}\n"
            "── Your turn ──\n"
            "You MUST do ALL of the following:\n"
            f"  1. REACT directly to {last_from}'s last message "
            "(agree, refine, challenge, build on it — be specific).\n"
            "  2. Add YOUR unique contribution based on your role.\n"
            "  3. Decide who in the swarm should handle this next "
            "— you may engage any peer, not just the one who sent to you.\n"
            "  4. Honestly assess: is the task now fully solved to a high "
            "standard? Set consensus=true ONLY if yes.\n\n"
            f"PEER AGENTS YOU CAN PASS TO: {peers}\n"
            "(Use 'TERMINATE' as next_agent if consensus=true and task is done.)\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "contribution": "your reaction + contribution (markdown OK, be thorough — 2-4 paragraphs)",\n'
            f'  "next_agent": "one name from {peers} or TERMINATE",\n'
            '  "consensus": false,\n'
            '  "reasoning": "one sentence: why this peer agent next"\n'
            "}"
        )

        raw  = generate_response(prompt, model_name=self.model_name)
        data = _extract_json(raw)

        # Validate next_agent — fall back to TERMINATE if unrecognised
        next_agent = data.get("next_agent", "TERMINATE")
        if next_agent not in peers and next_agent != "TERMINATE":
            next_agent = "TERMINATE"

        return {
            "contribution": data.get("contribution", raw),
            "next_agent":   next_agent,
            "consensus":    bool(data.get("consensus", False)),
            "reasoning":    data.get("reasoning", ""),
        }
