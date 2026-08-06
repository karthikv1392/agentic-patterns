"""Base agent — abstract class shared by all multi-agent patterns.

Design
------
Every concrete agent must supply:
  - name   : a human-readable label shown in the UI and logs.
  - persona: a system-level role description injected at the top of every
             prompt, shaping the agent's reasoning style.

Optionally override:
  - model_name : lets you mix different Gemini model variants across agents,
                 increasing ensemble diversity without changing logic.

Public API
----------
Pattern 01 — Voting Cooperation:
  respond(task)           ->  str    raw answer from this agent's perspective
  vote(task)              ->  dict   structured vote ready for the aggregator

Pattern 02 — Role-based Cooperation:
  execute(sub_task, prior_outputs)  ->  dict
      Runs the agent on its specialist sub-task, injecting accumulated
      outputs from all prior agents as shared memory context.

Pattern 03 — Debate-based Cooperation:
  debate(task, round_num, history)  ->  dict
      Round 0 : generate an independent initial position.
      Round N : read all prior-round responses from every other agent,
                then defend, revise, or challenge — advancing toward consensus.
"""

from abc import ABC, abstractmethod

from shared.llm import generate_response


class BaseAgent(ABC):
    """Abstract base for a voting agent in an ensemble.

    Subclass template
    -----------------
    class MyAgent(BaseAgent):
        def __init__(self):
            super().__init__(name="My Agent", model_name="gemma4")

        @property
        def persona(self) -> str:
            return "You are a ... analyst who always ..."
    """

    def __init__(self, name: str, model_name: str = "gemma4"):
        self._name = name
        self.model_name = model_name

    # ------------------------------------------------------------------
    # Identity — subclasses must implement persona
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    @abstractmethod
    def persona(self) -> str:
        """Return the system-level role description for this agent."""
        ...

    # ------------------------------------------------------------------
    # Core behaviour
    # ------------------------------------------------------------------

    def respond(self, task: str) -> str:
        """Generate a response to *task* through this agent's persona lens."""
        prompt = (
            f"{self.persona}\n\n"
            f"Task:\n{task}\n\n"
            "Provide a clear, well-reasoned response. "
            "Be concise but thorough — 2-4 paragraphs."
        )
        return generate_response(prompt, model_name=self.model_name)

    def vote(self, task: str) -> dict:
        """Return a structured vote dictionary for the aggregator.

        Returns
        -------
        {
            "agent_name" : str   — label of this agent
            "model"      : str   — Gemini model used
            "response"   : str   — full text answer
        }
        """
        response = self.respond(task)
        return {
            "agent_name": self.name,
            "model": self.model_name,
            "response": response,
        }

    # ------------------------------------------------------------------
    # Role-based cooperation API (Pattern 02)
    # ------------------------------------------------------------------

    @property
    def role(self) -> str:
        """Professional role title — override in role-based agents."""
        return self._name

    def execute(self, sub_task: str, prior_outputs: dict[str, str]) -> dict:
        """Execute a specialist sub-task with shared memory context.

        Parameters
        ----------
        sub_task      : the specific task assigned to this agent by the orchestrator
        prior_outputs : dict of {agent_name -> output} from agents that ran before

        Returns
        -------
        {
            "agent_name" : str   — label
            "role"       : str   — professional role title
            "model"      : str   — model used
            "sub_task"   : str   — what was assigned
            "output"     : str   — this agent's deliverable
        }
        """
        context_block = self._format_prior_outputs(prior_outputs)
        prompt = (
            f"{self.persona}\n\n"
            f"Your assigned task:\n{sub_task}\n\n"
            f"{context_block}"
            "Deliver your expert contribution. Use markdown formatting. "
            "Be specific and actionable."
        )
        output = generate_response(prompt, model_name=self.model_name)
        return {
            "agent_name": self.name,
            "role":       self.role,
            "model":      self.model_name,
            "sub_task":   sub_task,
            "output":     output,
        }

    @staticmethod
    def _format_prior_outputs(prior_outputs: dict[str, str]) -> str:
        """Format accumulated agent outputs as a context block."""
        if not prior_outputs:
            return ""
        lines = ["Work completed by prior team members (use as context):\n"]
        for agent_name, output in prior_outputs.items():
            lines.append(f"--- {agent_name} ---\n{output}\n")
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------
    # Debate-based cooperation API (Pattern 03)
    # ------------------------------------------------------------------

    def debate(self, task: str, round_num: int, history: list[dict]) -> dict:
        """Participate in one round of a structured multi-agent debate.

        Parameters
        ----------
        task      : the question / problem being debated
        round_num : 0 = opening statement, 1+ = rebuttal rounds
        history   : list of previous round dicts
                    [{"round": int, "responses": [{"agent_name", "response"}, ...]}, ...]

        Returns
        -------
        {"agent_name", "model", "round", "response"}
        """
        if round_num == 0:
            prompt = (
                f"{self.persona}\n\n"
                "You are participating in a structured multi-agent debate. "
                "Multiple agents with different perspectives will debate this topic "
                "across several rounds to reach the best possible answer.\n\n"
                f"Debate topic:\n{task}\n\n"
                "Present your opening position clearly and confidently. "
                "State your key arguments and the reasoning behind them. "
                "Take a definitive stance — be specific, not vague. (2-3 paragraphs)"
            )
        else:
            transcript = self._format_debate_history(history, exclude_agent=self.name)
            prompt = (
                f"{self.persona}\n\n"
                "You are in an ongoing structured debate. "
                f"This is round {round_num + 1}.\n\n"
                f"Debate topic:\n{task}\n\n"
                f"What others have argued so far:\n{transcript}\n"
                "--- Your turn ---\n"
                "You MUST do all of the following:\n"
                "  1. Address at least one specific argument made by another agent "
                "(name them explicitly — agree, refine, or rebut).\n"
                "  2. Either strengthen your previous position with new reasoning, "
                "OR revise it if another agent made a compelling point.\n"
                "  3. Identify any area of emerging agreement across agents.\n"
                "  4. End with a clear statement of where you currently stand.\n"
                "Be direct, specific, and push the debate toward a conclusion."
            )

        response = generate_response(prompt, model_name=self.model_name)
        return {
            "agent_name": self.name,
            "model":      self.model_name,
            "round":      round_num,
            "response":   response,
        }

    @staticmethod
    def _format_debate_history(history: list[dict], exclude_agent: str = "") -> str:
        """Render the debate transcript, optionally hiding one agent's own prior turns."""
        lines = []
        for round_data in history:
            rnum = round_data["round"]
            lines.append(f"\n── Round {rnum + 1} ──")
            for resp in round_data["responses"]:
                if resp["agent_name"] == exclude_agent:
                    lines.append(f"\n[{resp['agent_name']} — your previous position]:\n"
                                 f"{resp['response']}")
                else:
                    lines.append(f"\n[{resp['agent_name']}]:\n{resp['response']}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name!r}, model={self.model_name!r})"
