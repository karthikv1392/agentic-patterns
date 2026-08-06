"""Skill Agent — searches the library, solves tasks, and produces saveable skill metadata.

Two phases per task:

Phase 1 — Search
  The agent receives a list of skill *summaries* (no full solutions) and picks
  the top-K that are relevant to the current task.  Only the selected skills'
  full solutions are loaded for Phase 2.  This keeps the retrieval prompt lean
  regardless of library size.

Phase 2 — Solve
  The agent produces a complete solution and simultaneously generates the
  metadata needed to save it as a new skill (name, description, tags, type).
  If retrieved skills exist, the agent adapts/combines them; otherwise it
  works from scratch.  The `is_reusable` flag lets the agent opt out of
  saving solutions that are too task-specific to be useful later.
"""

import json
import re

from shared.base_agent import BaseAgent
from shared.llm import generate_response
from patterns.p11_skill_library.skill_store import Skill, SkillStore


def _extract_json(text: str) -> dict:
    """Extract the outermost JSON object from text (robust to embedded code)."""
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    # Fallback: greedy regex
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


class SkillAgent(BaseAgent):

    def __init__(self, store: SkillStore):
        super().__init__(name="SkillAgent", model_name="gemma4")
        self.store = store

    @property
    def persona(self) -> str:
        return (
            "You are an expert problem-solver who maintains a growing personal skill library. "
            "Before tackling any task you search your library for relevant prior solutions. "
            "You adapt and combine existing skills when possible, and always save valuable "
            "new solutions with clear metadata so future sessions can benefit from them."
        )

    # ------------------------------------------------------------------
    # Phase 1 — Search
    # ------------------------------------------------------------------

    def search_skills(self, task: str, top_k: int = 2) -> dict:
        """Find relevant skills in the library for the given task.

        Parameters
        ----------
        task  : The new task to solve.
        top_k : Maximum skills to retrieve (keeps solve prompt manageable).

        Returns
        -------
        {
            "retrieved"           : list[Skill],
            "retrieval_reasoning" : str,
            "skills_searched"     : int,
            "skipped"             : False,
        }
        """
        summaries = self.store.summaries_for_retrieval()
        if not summaries:
            return {
                "retrieved":           [],
                "retrieval_reasoning": "Library is empty — solving from scratch.",
                "skills_searched":     0,
                "skipped":             False,
            }

        summary_block = "\n".join(
            f'[{i+1}] id={s["id"]}\n'
            f'    Name: {s["name"]}  ({s["task_type"]})\n'
            f'    Tags: {", ".join(s["tags"])}\n'
            f'    Description: {s["description"]}\n'
            f'    Original task: {s["task_solved_preview"]}'
            for i, s in enumerate(summaries)
        )

        prompt = (
            f"{self.persona}\n\n"
            f"New task to solve:\n{task}\n\n"
            f"Your skill library ({len(summaries)} skills):\n{summary_block}\n\n"
            f"Identify up to {top_k} skills whose solutions could be REUSED, ADAPTED, "
            "or COMBINED to solve the new task. Only select skills with genuine overlap — "
            "do NOT select skills just because they share a broad topic.\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "relevant_skill_ids": ["<id>"],\n'
            '  "reasoning": "<2-3 sentences: which skills are relevant and why>"\n'
            "}"
        )

        raw  = generate_response(prompt, model_name=self.model_name)
        data = _extract_json(raw)

        retrieved_ids: list[str] = data.get("relevant_skill_ids", [])[:top_k]
        retrieved: list[Skill] = []
        for sid in retrieved_ids:
            skill = self.store.get(sid)
            if skill:
                retrieved.append(skill)
                self.store.increment_use(sid)

        return {
            "retrieved":           retrieved,
            "retrieval_reasoning": data.get("reasoning", ""),
            "skills_searched":     len(summaries),
            "skipped":             False,
        }

    # ------------------------------------------------------------------
    # Phase 2 — Solve
    # ------------------------------------------------------------------

    def solve(self, task: str, retrieved_skills: list[Skill]) -> dict:
        """Solve the task and generate metadata for saving as a new skill.

        Parameters
        ----------
        task             : The task to solve.
        retrieved_skills : Skills loaded from the library (may be empty).

        Returns
        -------
        {
            "solution"             : str,
            "approach"             : "from_scratch"|"adapted_from_skill"|"combined_skills",
            "skills_used"          : list[str],
            "is_reusable"          : bool,
            "suggested_name"       : str,
            "suggested_description": str,
            "suggested_tags"       : list[str],
            "task_type"            : str,
        }
        """
        if retrieved_skills:
            skills_block = "\n\n".join(
                f"=== Retrieved Skill: {s.name} ===\n"
                f"Description: {s.description}\n"
                f"Solution:\n{s.solution}"
                for s in retrieved_skills
            )
            approach_guidance = (
                "You have relevant existing skills (shown above). "
                "Build on them — adapt, extend, or combine them. "
                "Improve on their approach; do not copy verbatim."
            )
            default_approach = (
                "adapted_from_skill" if len(retrieved_skills) == 1 else "combined_skills"
            )
        else:
            skills_block     = "(none — library empty or no relevant skills found)"
            approach_guidance = "No relevant skills found. Produce a complete solution from scratch."
            default_approach  = "from_scratch"

        prompt = (
            f"{self.persona}\n\n"
            f"Task:\n{task}\n\n"
            f"Retrieved skills:\n{skills_block}\n\n"
            f"{approach_guidance}\n\n"
            "Also generate metadata so this solution can be saved as a skill.\n"
            "Set is_reusable=false ONLY if the answer is a one-off fact or too "
            "task-specific to ever help with a different task.\n\n"
            "Return ONLY valid JSON. For multi-line solution content, use \\n "
            "to represent newlines within the JSON string value:\n"
            "{\n"
            '  "solution": "<complete solution>",\n'
            f' "approach": "{default_approach}",\n'
            '  "skills_used": ["<skill name used>"],\n'
            '  "is_reusable": true,\n'
            '  "suggested_name": "<≤5 word skill name>",\n'
            '  "suggested_description": "<one sentence: what this skill does>",\n'
            '  "suggested_tags": ["<tag1>", "<tag2>", "<tag3>"],\n'
            '  "task_type": "Code|Analysis|Planning|Writing|General"\n'
            "}"
        )

        raw  = generate_response(prompt, model_name=self.model_name)
        data = _extract_json(raw)

        if not data.get("solution"):
            # Parsing failed — use the raw text as the solution
            data = {
                "solution":              raw.strip(),
                "approach":              default_approach,
                "skills_used":           [s.name for s in retrieved_skills],
                "is_reusable":           True,
                "suggested_name":        f"Skill: {task[:40]}",
                "suggested_description": f"Solution for: {task[:80]}",
                "suggested_tags":        [],
                "task_type":             "General",
            }

        return {
            "solution":              str(data.get("solution", raw.strip())),
            "approach":              str(data.get("approach", default_approach)),
            "skills_used":           list(data.get("skills_used", [])),
            "is_reusable":           bool(data.get("is_reusable", True)),
            "suggested_name":        str(data.get("suggested_name", "Unnamed Skill")),
            "suggested_description": str(data.get("suggested_description", "")),
            "suggested_tags":        list(data.get("suggested_tags", [])),
            "task_type":             str(data.get("task_type", "General")),
        }
