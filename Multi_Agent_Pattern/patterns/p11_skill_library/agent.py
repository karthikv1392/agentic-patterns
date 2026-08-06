"""Skill Library Evolution — entry point.

Pattern flow
------------
1. Search  — SkillAgent scans the persistent library for relevant prior skills.
             If the library is empty (or force_new=True), this phase is skipped.

2. Solve   — SkillAgent produces a solution.
             • If skills were retrieved: adapts / combines them as a starting point.
             • If no skills retrieved: works from scratch.
             The agent simultaneously drafts the metadata for saving this solution.

3. Save    — If the agent marks the solution as reusable (is_reusable=True), it is
             persisted to skill_library.json as a new named skill.  The library
             grows with every run, making future sessions progressively better.

Pre-seeded library
------------------
On the very first run (empty JSON file), three example skills are seeded so
retrieval can be demonstrated immediately.  Real systems accumulate organically.

Key distinction from p05 / p10
-------------------------------
Those patterns decompose a single task across multiple agents in parallel.
p11 is about *temporal* learning: the agent improves across sessions by building
and reusing a persistent knowledge base rather than always starting from scratch.
"""

from patterns.p11_skill_library.skill_store import Skill, SkillStore, make_skill
from patterns.p11_skill_library.skill_agent  import SkillAgent

# ---------------------------------------------------------------------------
# Singleton instances  (created once at import time)
# ---------------------------------------------------------------------------
STORE       = SkillStore()
SKILL_AGENT = SkillAgent(STORE)

# ---------------------------------------------------------------------------
# Pre-seeded skills
# ---------------------------------------------------------------------------
_SEED_SKILLS = [
    make_skill(
        name        = "SQL Injection Detector",
        description = "Detects common SQL injection patterns in a user-supplied string.",
        task_type   = "Code",
        tags        = ["sql", "security", "injection", "validation", "input-sanitization"],
        task_solved = "Write a function to detect SQL injection attempts in user input.",
        solution    = (
            'import re\n\n'
            'def detect_sql_injection(user_input: str) -> bool:\n'
            '    """Return True if *user_input* looks like a SQL injection attempt."""\n'
            '    patterns = [\n'
            "        r\"(\\x27|\\x22|;|--|#|\\/\\*|\\*\\/)\",         # quote/comment markers\n"
            '        r"\\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\\b",\n'
            '        r"(\\bOR\\b|\\bAND\\b)\\s+\\d+=\\d+",  # tautologies: OR 1=1\n'
            '        r"xp_\\w+",                            # MSSQL extended stored procs\n'
            '    ]\n'
            '    combined = "|".join(patterns)\n'
            '    return bool(re.search(combined, user_input, re.IGNORECASE))\n'
        ),
        created_at  = "2025-11-01T09:00:00+00:00",
    ),
    make_skill(
        name        = "Retry with Exponential Backoff",
        description = "Decorator that retries a function with exponential backoff on failure.",
        task_type   = "Code",
        tags        = ["retry", "resilience", "decorator", "backoff", "error-handling", "network"],
        task_solved = "Implement a retry mechanism with exponential backoff for flaky API calls.",
        solution    = (
            'import time, random, functools\n'
            'from typing import Callable, Type\n\n'
            'def retry_with_backoff(\n'
            '    max_attempts: int = 3,\n'
            '    base_delay: float = 1.0,\n'
            '    max_delay: float = 60.0,\n'
            '    exceptions: tuple[Type[Exception], ...] = (Exception,),\n'
            '    jitter: bool = True,\n'
            '):\n'
            '    """Retry decorator with exponential backoff.\n\n'
            '    Args:\n'
            '        max_attempts: Total tries (including first).\n'
            '        base_delay:   Initial wait seconds (doubles each retry).\n'
            '        max_delay:    Hard cap on wait time.\n'
            '        exceptions:   Exception types that trigger a retry.\n'
            '        jitter:       Add ±50 % random jitter to avoid thundering herd.\n'
            '    """\n'
            '    def decorator(func: Callable) -> Callable:\n'
            '        @functools.wraps(func)\n'
            '        def wrapper(*args, **kwargs):\n'
            '            delay = base_delay\n'
            '            for attempt in range(1, max_attempts + 1):\n'
            '                try:\n'
            '                    return func(*args, **kwargs)\n'
            '                except exceptions as exc:\n'
            '                    if attempt == max_attempts:\n'
            '                        raise\n'
            '                    wait = min(delay, max_delay)\n'
            '                    if jitter:\n'
            '                        wait *= 0.5 + random.random()\n'
            '                    print(f"Attempt {attempt} failed: {exc}. Retrying in {wait:.1f}s…")\n'
            '                    time.sleep(wait)\n'
            '                    delay *= 2\n'
            '        return wrapper\n'
            '    return decorator\n'
        ),
        created_at  = "2025-11-15T14:30:00+00:00",
    ),
    make_skill(
        name        = "Dict Schema Validator",
        description = "Validates a Python dict against a required-keys schema with type checks.",
        task_type   = "Code",
        tags        = ["validation", "schema", "dict", "type-checking", "data-quality"],
        task_solved = "Validate a data dictionary against a required schema with type checking.",
        solution    = (
            'def validate_schema(\n'
            '    data: dict,\n'
            '    schema: dict[str, type],\n'
            ') -> tuple[bool, list[str]]:\n'
            '    """Validate *data* against *schema*.\n\n'
            '    Args:\n'
            '        data:   The dict to validate.\n'
            '        schema: Mapping of required key -> expected type.\n\n'
            '    Returns:\n'
            '        (is_valid, errors) — errors is empty when valid.\n'
            '    """\n'
            '    errors: list[str] = []\n'
            '    for key, expected_type in schema.items():\n'
            '        if key not in data:\n'
            "            errors.append(f\"Missing required key: '{key}'\")\n"
            '            continue\n'
            '        if not isinstance(data[key], expected_type):\n'
            "            errors.append(\n"
            "                f\"Key '{key}': expected {getattr(expected_type, '__name__', str(expected_type))}, \"\n"
            "                f\"got {type(data[key]).__name__}\"\n"
            '            )\n'
            '    extra = set(data) - set(schema)\n'
            '    if extra:\n'
            "        errors.append(f\"Unexpected keys: {sorted(extra)}\")\n"
            '    return len(errors) == 0, errors\n'
        ),
        created_at  = "2025-12-01T11:00:00+00:00",
    ),
    make_skill(
        name        = "REST API Design Checklist",
        description = "A structured checklist covering the key concerns when designing a REST API.",
        task_type   = "Planning",
        tags        = ["api", "rest", "design", "checklist", "http", "architecture"],
        task_solved = "Create a checklist for designing a well-structured REST API.",
        solution    = (
            "## REST API Design Checklist\n\n"
            "### Resource Modelling\n"
            "- [ ] Use nouns for resource URLs (`/users`, `/orders`), not verbs\n"
            "- [ ] Nest sub-resources logically (`/users/{id}/orders`)\n"
            "- [ ] Prefer plural resource names consistently\n\n"
            "### HTTP Methods\n"
            "- [ ] GET  — read-only, safe, idempotent\n"
            "- [ ] POST — create; returns 201 + Location header\n"
            "- [ ] PUT  — full replace; idempotent\n"
            "- [ ] PATCH — partial update with explicit field list\n"
            "- [ ] DELETE — idempotent; 204 on success\n\n"
            "### Status Codes\n"
            "- [ ] 200/201/204 for success\n"
            "- [ ] 400 Bad Request with validation error body\n"
            "- [ ] 401 Unauthenticated / 403 Unauthorized\n"
            "- [ ] 404 Not Found / 409 Conflict / 422 Unprocessable\n"
            "- [ ] 429 Rate Limited with Retry-After header\n"
            "- [ ] 500 — never leak stack traces\n\n"
            "### Auth & Security\n"
            "- [ ] Bearer token (JWT) or API key via Authorization header\n"
            "- [ ] HTTPS only; HSTS enabled\n"
            "- [ ] Rate limiting + throttling per client\n"
            "- [ ] Input validation and output sanitization\n\n"
            "### Pagination & Filtering\n"
            "- [ ] Cursor-based or offset pagination for list endpoints\n"
            "- [ ] Filter via query params (`?status=active&sort=created_at`)\n"
            "- [ ] Return total count + next/prev cursor in response envelope\n\n"
            "### Versioning\n"
            "- [ ] Version in URL path (`/v1/`) or Accept header\n"
            "- [ ] Deprecation notices in response headers\n\n"
            "### Documentation\n"
            "- [ ] OpenAPI / Swagger spec auto-generated from code\n"
            "- [ ] Example request + response for every endpoint\n"
            "- [ ] Error catalogue with codes and remediation guidance\n"
        ),
        created_at  = "2025-12-10T08:00:00+00:00",
    ),
]


def seed_library(store: SkillStore):
    """Populate the library with starter skills if it is empty."""
    if store.size() == 0:
        for skill in _SEED_SKILLS:
            store.add(skill)


# Seed on first import (only runs once, when JSON file doesn't exist / is empty)
seed_library(STORE)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(task: str, force_new: bool = False) -> dict:
    """Run the full Skill Library Evolution pipeline.

    Parameters
    ----------
    task      : The task to solve.
    force_new : If True, skip skill retrieval and solve from scratch.
                The solution is still evaluated and may be saved to the library.

    Returns
    -------
    {
        "task"                : str,
        "force_new"           : bool,
        "library_size_before" : int,
        "search"              : {
            "retrieved"           : list[dict],   — serialised Skill dicts
            "retrieval_reasoning" : str,
            "skills_searched"     : int,
            "skipped"             : bool,
        },
        "solution"            : dict,             — solve result
        "skill_saved"         : dict | None,      — serialised new Skill, or None
        "library_size_after"  : int,
        "library_stats"       : dict,
    }
    """
    library_size_before = STORE.size()

    # ── Step 1: Search ─────────────────────────────────────────────────────
    if force_new or library_size_before == 0:
        search_result: dict = {
            "retrieved":           [],
            "retrieval_reasoning": (
                "Force-new mode — library search skipped."
                if force_new else
                "Library is empty — solving from scratch."
            ),
            "skills_searched":     library_size_before,
            "skipped":             True,
        }
    else:
        search_result = SKILL_AGENT.search_skills(task, top_k=2)

    # ── Step 2: Solve ──────────────────────────────────────────────────────
    solution_result = SKILL_AGENT.solve(
        task             = task,
        retrieved_skills = search_result["retrieved"],   # list[Skill]
    )

    # ── Step 3: Save ───────────────────────────────────────────────────────
    skill_saved: Skill | None = None
    if solution_result["is_reusable"]:
        skill_saved = STORE.add(
            make_skill(
                name        = solution_result["suggested_name"],
                description = solution_result["suggested_description"],
                task_type   = solution_result["task_type"],
                tags        = solution_result["suggested_tags"],
                task_solved = task,
                solution    = solution_result["solution"],
            )
        )

    def _skill_to_dict(s: Skill) -> dict:
        return {
            "id":          s.id,
            "name":        s.name,
            "description": s.description,
            "task_type":   s.task_type,
            "tags":        s.tags,
            "task_solved": s.task_solved,
            "use_count":   s.use_count,
            "created_at":  s.created_at,
        }

    return {
        "task":                task,
        "force_new":           force_new,
        "library_size_before": library_size_before,
        "search": {
            **search_result,
            # Serialise Skill objects → plain dicts for the UI
            "retrieved": [_skill_to_dict(s) for s in search_result["retrieved"]],
        },
        "solution":            solution_result,
        "skill_saved":         _skill_to_dict(skill_saved) if skill_saved else None,
        "library_size_after":  STORE.size(),
        "library_stats":       STORE.stats(),
    }
