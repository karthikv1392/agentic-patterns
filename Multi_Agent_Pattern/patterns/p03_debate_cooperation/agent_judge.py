"""Judge Agent — Debate-based Cooperation pattern.

Role
----
The Judge is NOT a debater. It reads the complete debate transcript after
all rounds have completed and produces the final verdict:

  • Which arguments were strongest and why
  • Where genuine consensus emerged across debaters
  • Where meaningful disagreement remains
  • Whether any agent visibly changed position (and what convinced them)
  • A final, synthesised answer that represents the best conclusion

The Judge does not pick a "winner" — it synthesises the debate into
the most defensible, well-rounded final position.
"""

import json
import re

from shared.base_agent import BaseAgent
from shared.llm import generate_response


class JudgeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Judge",
            model_name="gemma4",
        )

    @property
    def persona(self) -> str:
        return (
            "You are an impartial, senior judge evaluating a structured debate. "
            "You read every argument carefully, weigh evidence and reasoning, "
            "identify where agents agree and where they genuinely differ, "
            "and synthesise the strongest possible final answer."
        )

    def adjudicate(self, task: str, debate_history: list[dict]) -> dict:
        """Read the full debate transcript and produce a structured verdict.

        Returns
        -------
        {
            "key_agreements"     : list[str]  — points all/most agents agreed on
            "key_disagreements"  : list[str]  — unresolved points of contention
            "position_changes"   : list[str]  — agents who visibly shifted position
            "strongest_argument" : str        — the single most compelling argument made
            "consensus_reached"  : bool       — whether a clear consensus emerged
            "final_answer"       : str        — the judge's synthesised conclusion
            "reasoning"          : str        — why this is the best conclusion
        }
        """
        transcript = self._format_debate_history(debate_history)

        prompt = (
            f"{self.persona}\n\n"
            f"Debate topic:\n{task}\n\n"
            f"Full debate transcript:\n{transcript}\n\n"
            "After reading all rounds carefully, produce your verdict. Return ONLY valid JSON:\n"
            "{\n"
            '  "key_agreements":     ["point agents agreed on", ...],\n'
            '  "key_disagreements":  ["unresolved contention", ...],\n'
            '  "position_changes":   ["Agent X shifted from Y to Z because ...", ...],\n'
            '  "strongest_argument": "the single most compelling argument made and by whom",\n'
            '  "consensus_reached":  true or false,\n'
            '  "final_answer":       "your synthesised conclusion (markdown OK, be thorough)",\n'
            '  "reasoning":          "why this is the best conclusion given the debate"\n'
            "}"
        )

        raw = generate_response(prompt, model_name=self.model_name)
        data = self._extract_json(raw)

        return {
            "key_agreements":     data.get("key_agreements",     []),
            "key_disagreements":  data.get("key_disagreements",  []),
            "position_changes":   data.get("position_changes",   []),
            "strongest_argument": data.get("strongest_argument", ""),
            "consensus_reached":  data.get("consensus_reached",  False),
            "final_answer":       data.get("final_answer",       raw),
            "reasoning":          data.get("reasoning",          ""),
        }

    @staticmethod
    def _extract_json(text: str) -> dict:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}
