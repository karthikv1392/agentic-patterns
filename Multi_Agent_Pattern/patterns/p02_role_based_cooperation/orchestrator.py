"""Orchestrator — divides the user task into role-specific sub-tasks.

The orchestrator is a lightweight LLM call that reads the overall task and
produces a tailored assignment for each specialist role in the pipeline.
This ensures agents receive targeted instructions rather than the raw prompt,
making each agent's output focused and relevant to their expertise.

Shared Memory
-------------
After the orchestrator produces assignments, the pipeline passes a growing
`shared_memory` dict from agent to agent:

    shared_memory = {}
    for agent in [pm, architect, developer, qa]:
        result = agent.execute(assignments[agent.name], shared_memory)
        shared_memory[agent.name] = result["output"]   # handoff to next agent

Each agent sees the full accumulated output of all prior agents, simulating
a real team where later members can read earlier deliverables.
"""

import json
import re

from shared.llm import generate_response

# The ordered sequence of roles in the pipeline
PIPELINE_ROLES = [
    "Product Manager",
    "System Architect",
    "Senior Developer",
    "QA Engineer",
]


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def divide_task(task: str) -> dict:
    """Use an LLM to split the overall task into per-role sub-tasks.

    Parameters
    ----------
    task : the user's original high-level task

    Returns
    -------
    dict mapping each role name to its specific assignment string, e.g.:
    {
        "Product Manager":   "Define requirements and success criteria for ...",
        "System Architect":  "Design the technical architecture for ...",
        "Senior Developer":  "Create an implementation plan for ...",
        "QA Engineer":       "Develop a test strategy for ...",
    }
    """
    roles_list = "\n".join(f"- {r}" for r in PIPELINE_ROLES)

    prompt = (
        "You are a project orchestrator assigning work to a specialist team. "
        "Given the overall task below, write a specific, focused sub-task "
        "for each team member. Each sub-task should:\n"
        "  • Be written directly to that specialist (use 'you' / imperative voice).\n"
        "  • Stay within their area of expertise.\n"
        "  • Reference the overall goal so they have context.\n"
        "  • Be 2-4 sentences — enough to guide them without being prescriptive.\n\n"
        f"Overall task:\n{task}\n\n"
        f"Team roles:\n{roles_list}\n\n"
        "Return ONLY valid JSON with exactly these keys:\n"
        "{\n"
        '  "Product Manager":  "sub-task text",\n'
        '  "System Architect": "sub-task text",\n'
        '  "Senior Developer": "sub-task text",\n'
        '  "QA Engineer":      "sub-task text"\n'
        "}"
    )

    raw = generate_response(prompt)
    assignments = _extract_json(raw)

    # Fallback: if JSON parsing fails, give each agent the full task
    for role in PIPELINE_ROLES:
        if role not in assignments:
            assignments[role] = (
                f"As the {role}, apply your expertise to this task: {task}"
            )

    return assignments


def synthesise(task: str, shared_memory: dict[str, str]) -> str:
    """Produce a final integrated document from all agent outputs.

    Parameters
    ----------
    task          : original user task (for context)
    shared_memory : {agent_name -> output} from all pipeline agents

    Returns
    -------
    A cohesive final deliverable combining all specialist contributions.
    """
    contributions = "\n\n".join(
        f"=== {name} ===\n{output}"
        for name, output in shared_memory.items()
    )

    prompt = (
        "You are a senior technical writer and project lead. "
        "A specialist team has each produced their expert contribution to the task below. "
        "Synthesise all contributions into one cohesive, well-structured final document.\n\n"
        f"Original task:\n{task}\n\n"
        f"Team contributions:\n{contributions}\n\n"
        "Write the final integrated document. Use clear markdown headings for each section. "
        "Resolve any conflicts or gaps between the contributions. "
        "The result should read as a single unified deliverable, not a collection of excerpts."
    )

    return generate_response(prompt)
