"""Dispatcher — entry point and communication facilitator of the swarm.

The Dispatcher is NOT an orchestrator. It has two narrow responsibilities:

1. START: Analyse the incoming task and decide which swarm agent is best
   placed to open the conversation. It does not plan the full route — it
   just makes the first handoff.

2. END: After the swarm terminates (by consensus or max iterations),
   synthesise the full conversation into a clean final answer. As the
   facilitator that observed every message, it is uniquely positioned
   to integrate the collective output.

What the Dispatcher does NOT do
--------------------------------
- It does not control which agent speaks next (that is each agent's choice).
- It does not evaluate or score agent outputs mid-swarm.
- It does not re-route or override agent-to-agent handoffs.
"""

import json
import re

from shared.base_agent import BaseAgent
from shared.llm import generate_response


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


class DispatcherAgent(BaseAgent):
    """Swarm entry-point and post-swarm synthesiser."""

    def __init__(self):
        super().__init__(name="Dispatcher", model_name="gemma4")

    @property
    def persona(self) -> str:
        return (
            "You are a Dispatcher — the entry point of a multi-agent swarm. "
            "Your role is NOT to solve tasks yourself but to:\n"
            "  1. Identify the best first swarm agent to engage for a given task.\n"
            "  2. After the swarm completes, synthesise all agent contributions "
            "into a coherent, high-quality final answer.\n"
            "You are neutral, observant, and focused on the quality of the collective output."
        )

    # ------------------------------------------------------------------
    # Role 1 — Select the first swarm agent
    # ------------------------------------------------------------------

    def select_first(self, task: str, agent_names: list[str]) -> dict:
        """Decide which swarm agent should open the conversation.

        Parameters
        ----------
        task        : The task the swarm will tackle.
        agent_names : Names of all available swarm agents.

        Returns
        -------
        {
            "first_agent" : str   — name of the first agent to engage
            "reasoning"   : str   — why this agent was chosen
        }
        """
        prompt = (
            f"{self.persona}\n\n"
            "A new task has arrived for the swarm. "
            "Your job is to decide which agent should handle it first.\n\n"
            f"Task:\n{task}\n\n"
            f"Available swarm agents: {agent_names}\n\n"
            "Consider each agent's specialisation and choose the one best "
            "positioned to make a strong opening contribution. "
            "The other agents will naturally engage from there.\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            f'  "first_agent": "one name from {agent_names}",\n'
            '  "reasoning": "one sentence: why this agent is best to start"\n'
            "}"
        )
        raw  = generate_response(prompt, model_name=self.model_name)
        data = _extract_json(raw)

        chosen = data.get("first_agent", "")
        if chosen not in agent_names:
            chosen = agent_names[0]  # fallback to first available

        return {
            "first_agent": chosen,
            "reasoning":   data.get("reasoning", "Default selection."),
        }

    # ------------------------------------------------------------------
    # Role 2 — Synthesise the swarm output
    # ------------------------------------------------------------------

    def synthesise(self, task: str, history: list[dict]) -> str:
        """Produce the final answer from the full swarm conversation.

        Parameters
        ----------
        task    : The original task.
        history : All swarm messages (in order).
        """
        transcript = "\n\n".join(
            f"[{msg['from_agent']} → {msg['next_agent']}]:\n{msg['content']}"
            for msg in history
        )
        prompt = (
            f"{self.persona}\n\n"
            "The swarm has completed its work. "
            "Below is the full agent conversation.\n\n"
            f"Original task:\n{task}\n\n"
            f"Swarm transcript:\n{transcript}\n\n"
            "Synthesise the collective swarm output into a definitive final answer. "
            "Integrate the best ideas, critiques, refinements, and validations "
            "from all agents. Resolve any tensions or contradictions. "
            "Produce a clear, well-structured response in markdown. "
            "Do not just concatenate — actively synthesise and elevate. 400-700 words."
        )
        return generate_response(prompt, model_name=self.model_name)
