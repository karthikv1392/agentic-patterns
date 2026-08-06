"""Skill Store — persistent skill library backed by a JSON file.

Each Skill captures:
  - name + description  : human-readable identity
  - task_type           : Code | Analysis | Planning | Writing | General
  - tags                : keywords for LLM-powered retrieval
  - task_solved         : the original task that created this skill
  - solution            : the reusable output (code, plan, text, etc.)
  - created_at          : ISO 8601 timestamp
  - use_count           : how many future sessions retrieved this skill
  - author              : which agent (or human) contributed it

The library persists to skill_library.json in this directory.
Skills accumulate with every run — the agent gets better over time.
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

LIBRARY_PATH = Path(__file__).parent / "skill_library.json"

TASK_TYPES = ["Code", "Analysis", "Planning", "Writing", "General"]


@dataclass
class Skill:
    id:           str
    name:         str
    description:  str
    task_type:    str           # Code | Analysis | Planning | Writing | General
    tags:         list[str]
    task_solved:  str           # the original task prompt
    solution:     str           # the reusable output
    created_at:   str           # ISO 8601
    use_count:    int = 0       # times retrieved by future sessions
    author:       str = "SkillAgent"


def make_skill(
    name:        str,
    description: str,
    task_type:   str,
    tags:        list[str],
    task_solved: str,
    solution:    str,
    author:      str = "SkillAgent",
    created_at:  str | None = None,
) -> Skill:
    """Factory — creates a Skill with a fresh UUID and timestamp."""
    return Skill(
        id          = str(uuid.uuid4()),
        name        = name,
        description = description,
        task_type   = task_type,
        tags        = tags,
        task_solved = task_solved,
        solution    = solution,
        created_at  = created_at or datetime.now(timezone.utc).isoformat(),
        use_count   = 0,
        author      = author,
    )


class SkillStore:
    """JSON-backed persistent skill library.

    Thread-safety note: reads/writes happen synchronously; fine for the
    single-user Streamlit demo. A production system would use a DB with
    proper concurrency controls.
    """

    def __init__(self, path: Path = LIBRARY_PATH):
        self.path = path
        self._skills: dict[str, Skill] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
            for item in data.get("skills", []):
                skill = Skill(**item)
                self._skills[skill.id] = skill
        except (json.JSONDecodeError, TypeError, KeyError):
            pass  # corrupted file — start fresh

    def _persist(self):
        data = {"skills": [asdict(s) for s in self._skills.values()]}
        self.path.write_text(json.dumps(data, indent=2))

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------

    def add(self, skill: Skill) -> Skill:
        """Add a skill and persist immediately."""
        self._skills[skill.id] = skill
        self._persist()
        return skill

    def increment_use(self, skill_id: str):
        """Bump the use_count for a retrieved skill."""
        if skill_id in self._skills:
            self._skills[skill_id].use_count += 1
            self._persist()

    def clear(self):
        """Remove ALL skills (used for reset)."""
        self._skills = {}
        self._persist()

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def get(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def all_skills(self) -> list[Skill]:
        """Return all skills sorted newest-first."""
        return sorted(self._skills.values(), key=lambda s: s.created_at, reverse=True)

    def size(self) -> int:
        return len(self._skills)

    def stats(self) -> dict:
        skills = self.all_skills()
        if not skills:
            return {
                "total_skills": 0,
                "total_uses":   0,
                "task_types":   {},
                "most_used":    None,
                "newest":       None,
            }
        type_counts: dict[str, int] = {}
        for s in skills:
            type_counts[s.task_type] = type_counts.get(s.task_type, 0) + 1

        by_uses   = sorted(skills, key=lambda s: s.use_count, reverse=True)
        most_used = by_uses[0] if by_uses[0].use_count > 0 else None

        return {
            "total_skills": len(skills),
            "total_uses":   sum(s.use_count for s in skills),
            "task_types":   type_counts,
            "most_used":    most_used.name if most_used else None,
            "newest":       skills[0].name,
        }

    def summaries_for_retrieval(self) -> list[dict]:
        """Lightweight skill summaries for the LLM retrieval call.

        Full solutions are NOT sent here — they're fetched only for
        the skills that are actually retrieved, keeping the prompt small.
        """
        return [
            {
                "id":                 s.id,
                "name":               s.name,
                "description":        s.description,
                "task_type":          s.task_type,
                "tags":               s.tags,
                "task_solved_preview": s.task_solved[:180],
            }
            for s in self.all_skills()
        ]
