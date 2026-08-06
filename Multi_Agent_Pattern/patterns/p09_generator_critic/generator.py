"""Generator Agent — produces drafts and refines them based on critic feedback.

The GeneratorAgent is the creative half of the Generator-Critic loop.
  - Iteration 1: cold-start generation given just the task and draft_type.
  - Iteration 2+: takes previous_draft + critic's must-fix issues + overall_feedback
                  and produces a refined version that explicitly addresses each issue.

Returns a dict: {"draft": str, "version": int, "rationale": str}
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


class GeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Generator", model_name="gemma4")

    @property
    def persona(self) -> str:
        return (
            "You are an expert drafter with deep experience producing high-quality "
            "outputs across code, text, plans, and professional communications. "
            "You are meticulous, precise, and always aim to address every concern raised."
        )

    def generate(
        self,
        task: str,
        draft_type: str,
        iteration: int = 1,
        previous_draft: str | None = None,
        critic_feedback: dict | None = None,
    ) -> dict:
        """Produce or refine a draft.

        Parameters
        ----------
        task            : The original task description.
        draft_type      : One of "Code", "Text", "Plan", "Email".
        iteration       : 1 for cold start, 2+ for refinement.
        previous_draft  : The previous draft text (required for iteration >= 2).
        critic_feedback : The critic's full critique dict (required for iteration >= 2).

        Returns
        -------
        {"draft": str, "version": int, "rationale": str}
        """
        if iteration == 1:
            prompt = self._build_cold_start_prompt(task, draft_type)
        else:
            prompt = self._build_refinement_prompt(
                task, draft_type, iteration, previous_draft, critic_feedback
            )

        raw = generate_response(prompt, model_name=self.model_name)
        data = _extract_json(raw)

        # If JSON extraction fails, treat the entire response as the draft
        if not data or "draft" not in data:
            data = {
                "draft": raw.strip(),
                "version": iteration,
                "rationale": "Generated draft.",
            }

        return {
            "draft": str(data.get("draft", raw.strip())),
            "version": iteration,
            "rationale": str(data.get("rationale", "Draft produced.")),
        }

    def _build_cold_start_prompt(self, task: str, draft_type: str) -> str:
        type_guidance = {
            "Code": (
                "Write correct, secure, efficient, readable code with proper error handling. "
                "Include docstrings and comments where helpful."
            ),
            "Text": (
                "Write clear, coherent, accurate, well-styled and complete text. "
                "Structure it logically with good flow."
            ),
            "Plan": (
                "Create a feasible, complete plan that addresses risks, is clear, "
                "and is broken into actionable steps."
            ),
            "Email": (
                "Write a professional email with the right tone, clear message, "
                "concise language, and a clear call to action."
            ),
        }.get(draft_type, "Produce a high-quality output for the given task.")

        return (
            f"{self.persona}\n\n"
            f"Task:\n{task}\n\n"
            f"Draft type: {draft_type}\n"
            f"Guidance: {type_guidance}\n\n"
            "Produce your best first draft.\n\n"
            "Return ONLY valid JSON in this exact format:\n"
            "{\n"
            '  "draft": "<your full draft here>",\n'
            '  "rationale": "<brief explanation of your approach and key decisions>"\n'
            "}"
        )

    def _build_refinement_prompt(
        self,
        task: str,
        draft_type: str,
        iteration: int,
        previous_draft: str,
        critic_feedback: dict,
    ) -> str:
        must_fix = critic_feedback.get("must_fix", [])
        overall_feedback = critic_feedback.get("overall_feedback", "")
        overall_score = critic_feedback.get("overall_score", "?")

        must_fix_block = ""
        if must_fix:
            issues = "\n".join(f"  {i+1}. {issue}" for i, issue in enumerate(must_fix))
            must_fix_block = f"\nMUST-FIX issues (address ALL of these):\n{issues}\n"

        return (
            f"{self.persona}\n\n"
            f"You are refining a {draft_type} draft (iteration {iteration}).\n\n"
            f"Original task:\n{task}\n\n"
            f"Previous draft (version {iteration - 1}):\n{previous_draft}\n\n"
            f"Critic's overall score: {overall_score}/10\n"
            f"Critic's overall feedback: {overall_feedback}\n"
            f"{must_fix_block}\n"
            "Produce an improved version that explicitly addresses EVERY must-fix issue. "
            "Do not regress on aspects that were already good.\n\n"
            "Return ONLY valid JSON in this exact format:\n"
            "{\n"
            '  "draft": "<your full improved draft here>",\n'
            '  "rationale": "<brief explanation of what you changed and why>"\n'
            "}"
        )
