"""Initiator — decomposes a complex task into N independent sub-tasks.

The Initiator is the first step of the Parallel/Fan-Out pattern. It uses an
LLM to analyse the incoming task and split it into self-contained sub-tasks
that can each be tackled by a different specialist agent simultaneously.

Key property: sub-tasks must be *independent* — no sub-task should require
the output of another sub-task as input.
"""

import json
import re

from shared.llm import generate_response


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def decompose(task: str, num_subtasks: int = 3) -> dict:
    """Break *task* into *num_subtasks* independent sub-tasks.

    Parameters
    ----------
    task         : The complex task / question to decompose.
    num_subtasks : How many parallel branches to create (2-4).

    Returns
    -------
    {
        "overview"  : str  — decomposition strategy summary
        "sub_tasks" : [
            {
                "index"       : int   — 1-based position
                "title"       : str   — short label for the sub-task
                "description" : str   — what the specialist should do
                "focus"       : str   — research | analysis | strategy | critique
            },
            ...
        ]
    }
    """
    focus_options = ["research", "analysis", "strategy", "critique"]
    assigned_focuses = focus_options[:num_subtasks]

    prompt = (
        "You are a task-decomposition expert. Your job is to split a complex task "
        "into exactly {n} *independent* sub-tasks that different specialist agents "
        "can work on simultaneously — no sub-task should depend on the output of "
        "another.\n\n"
        "Task:\n{task}\n\n"
        "Decompose into exactly {n} sub-tasks, each covering a distinct dimension:\n"
        "{focuses}\n\n"
        "Return ONLY valid JSON:\n"
        "{{\n"
        '  "overview": "one-sentence decomposition strategy",\n'
        '  "sub_tasks": [\n'
        '    {{\n'
        '      "index": 1,\n'
        '      "title": "short title",\n'
        '      "description": "2-3 sentences describing exactly what this agent should do",\n'
        '      "focus": "research|analysis|strategy|critique"\n'
        '    }},\n'
        "    ...\n"
        "  ]\n"
        "}}"
    ).format(
        n=num_subtasks,
        task=task,
        focuses="\n".join(f"  {i+1}. {f}" for i, f in enumerate(assigned_focuses)),
    )

    raw = generate_response(prompt)
    data = _extract_json(raw)

    if data.get("sub_tasks"):
        return data

    # Fallback: generic split
    return {
        "overview": f"Generic {num_subtasks}-way decomposition of the task.",
        "sub_tasks": [
            {
                "index": i + 1,
                "title": f"{f.title()} perspective",
                "description": (
                    f"Approach the following task from a {f} perspective: {task}"
                ),
                "focus": f,
            }
            for i, f in enumerate(assigned_focuses)
        ],
    }
