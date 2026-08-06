"""Critic Agent — evaluates drafts against domain-specific quality criteria.

The CriticAgent is the evaluative half of the Generator-Critic loop.
It scores each criterion 1-10 and determines whether the draft passes.

Passing threshold: overall_score >= 7 AND must_fix list is empty.

Returns a dict:
{
    "passed": bool,
    "overall_score": int,
    "criteria_scores": {
        criterion: {"score": int, "feedback": str, "severity": "ok"|"must_fix"|"nice_to_have"}
    },
    "overall_feedback": str,
    "must_fix": [str],
    "passed_criteria": int,
    "total_criteria": int,
}
"""

import json
import re

from shared.base_agent import BaseAgent
from shared.llm import generate_response


CRITERIA_BY_TYPE = {
    "Code":  ["correctness", "security", "efficiency", "readability", "error_handling"],
    "Text":  ["clarity", "coherence", "accuracy", "style", "completeness"],
    "Plan":  ["feasibility", "completeness", "risk_awareness", "clarity", "actionability"],
    "Email": ["tone", "clarity", "professionalism", "conciseness", "call_to_action"],
}


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Critic", model_name="gemma4")

    @property
    def persona(self) -> str:
        return (
            "You are a rigorous quality reviewer with extremely high standards. "
            "You evaluate work objectively against specific criteria, provide actionable "
            "feedback, and only approve work that genuinely meets a high quality bar. "
            "A score of 7+ means the criterion is genuinely good, not just passable."
        )

    def critique(
        self,
        draft: str,
        task: str,
        draft_type: str,
        iteration: int,
    ) -> dict:
        """Evaluate a draft against domain-specific criteria.

        Parameters
        ----------
        draft      : The draft text to evaluate.
        task       : The original task description.
        draft_type : One of "Code", "Text", "Plan", "Email".
        iteration  : Which iteration this critique is for (informational).

        Returns
        -------
        {
            "passed": bool,
            "overall_score": int,
            "criteria_scores": {criterion: {"score", "feedback", "severity"}},
            "overall_feedback": str,
            "must_fix": [str],
            "passed_criteria": int,
            "total_criteria": int,
        }
        """
        criteria = CRITERIA_BY_TYPE.get(draft_type, CRITERIA_BY_TYPE["Text"])
        prompt = self._build_prompt(draft, task, draft_type, criteria, iteration)

        raw = generate_response(prompt, model_name=self.model_name)
        data = _extract_json(raw)

        return self._parse_response(data, criteria)

    def _build_prompt(
        self,
        draft: str,
        task: str,
        draft_type: str,
        criteria: list[str],
        iteration: int,
    ) -> str:
        criteria_lines = "\n".join(
            f'  - "{c}": score 1-10, feedback string, severity ("ok"|"must_fix"|"nice_to_have")'
            for c in criteria
        )
        criteria_json_template = ", ".join(
            f'"{c}": {{"score": <1-10>, "feedback": "<string>", "severity": "ok|must_fix|nice_to_have"}}'
            for c in criteria
        )

        return (
            f"{self.persona}\n\n"
            f"You are reviewing a {draft_type} draft (iteration {iteration}).\n\n"
            f"Original task:\n{task}\n\n"
            f"Draft to evaluate:\n{draft}\n\n"
            f"Evaluate against these {len(criteria)} criteria:\n"
            f"{criteria_lines}\n\n"
            "Scoring rules:\n"
            "  • 1-4: Unacceptable — fundamental issues, must_fix severity\n"
            "  • 5-6: Below par — notable issues, must_fix for critical aspects\n"
            "  • 7-8: Good — minor issues at most, nice_to_have severity\n"
            "  • 9-10: Excellent — no significant issues, ok severity\n\n"
            "A draft PASSES if its overall_score >= 7 AND there are zero must_fix issues.\n\n"
            "must_fix list: include a brief description for every criterion with severity=must_fix.\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            f'  "criteria_scores": {{{criteria_json_template}}},\n'
            '  "overall_score": <1-10 weighted average>,\n'
            '  "overall_feedback": "<2-3 sentence summary of strengths and weaknesses>",\n'
            '  "must_fix": ["<issue description>", ...]\n'
            "}"
        )

    def _parse_response(self, data: dict, criteria: list[str]) -> dict:
        criteria_scores = data.get("criteria_scores", {})
        overall_score = int(data.get("overall_score", 5))
        overall_score = max(1, min(10, overall_score))
        overall_feedback = data.get("overall_feedback", "Critique completed.")
        must_fix = data.get("must_fix", [])
        if not isinstance(must_fix, list):
            must_fix = []

        # Normalize criteria_scores: ensure all criteria are present
        normalized = {}
        for c in criteria:
            entry = criteria_scores.get(c, {})
            score = int(entry.get("score", 5))
            score = max(1, min(10, score))
            feedback = str(entry.get("feedback", "No feedback provided."))
            severity = str(entry.get("severity", "must_fix" if score < 7 else "ok"))
            if severity not in ("ok", "must_fix", "nice_to_have"):
                severity = "must_fix" if score < 7 else "ok"
            normalized[c] = {"score": score, "feedback": feedback, "severity": severity}

        # Recompute must_fix from criteria if LLM didn't populate it well
        if not must_fix:
            must_fix = [
                f"{c}: {normalized[c]['feedback']}"
                for c in criteria
                if normalized[c]["severity"] == "must_fix"
            ]

        passed_criteria = sum(1 for c in criteria if normalized[c]["score"] >= 7)
        passed = overall_score >= 7 and len(must_fix) == 0

        return {
            "passed": passed,
            "overall_score": overall_score,
            "criteria_scores": normalized,
            "overall_feedback": overall_feedback,
            "must_fix": must_fix,
            "passed_criteria": passed_criteria,
            "total_criteria": len(criteria),
        }
