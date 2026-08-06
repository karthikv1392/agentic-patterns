"""Action Planner — decomposes a task into a sequence of discrete, executable actions.

The planner is domain-aware: it generates realistic actions that an autonomous
agent would actually take in that environment (clinical, trading, DevOps, etc.).
It deliberately includes a mix of routine and high-impact actions so that the
risk classification and approval flow are meaningful.
"""

import json
import re

from shared.llm import generate_response


DOMAIN_CONTEXTS = {
    "Clinical": (
        "clinical healthcare system with strict patient safety and HIPAA compliance requirements. "
        "Actions may include reading patient records, prescribing medications, ordering labs, "
        "scheduling procedures, or updating treatment plans."
    ),
    "Trading": (
        "financial trading platform with SEC/MiFID regulatory compliance. "
        "Actions may include reading market data, placing buy/sell orders, rebalancing portfolios, "
        "executing large block trades, or modifying risk limits."
    ),
    "DevOps": (
        "production infrastructure environment with SLA and uptime requirements. "
        "Actions may include running diagnostics, deploying code, scaling services, "
        "modifying firewall rules, rolling back deployments, or rotating secrets."
    ),
    "Custom": (
        "general enterprise environment. "
        "Actions may include reading data, sending communications, modifying records, "
        "executing processes, or interacting with external systems."
    ),
}


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def plan_actions(task: str, domain: str, num_actions: int = 6) -> dict:
    """Decompose a task into a sequence of discrete agent actions.

    Parameters
    ----------
    task        : The task the agent needs to accomplish.
    domain      : "Clinical" | "Trading" | "DevOps" | "Custom"
    num_actions : How many actions to generate (5-6 recommended).

    Returns
    -------
    {
        "task_summary" : str
        "domain"       : str
        "actions"      : [
            {
                "index"            : int
                "action"           : str   — concrete description
                "type"             : str   — read|write|execute|communicate|modify|delete
                "target"           : str   — what system/data/entity is affected
                "expected_outcome" : str   — what happens if this executes
            },
            ...
        ]
    }
    """
    context = DOMAIN_CONTEXTS.get(domain, DOMAIN_CONTEXTS["Custom"])

    prompt = (
        f"You are an autonomous agent operating in a {context}\n\n"
        f"You have been asked to: {task}\n\n"
        f"Break this task into exactly {num_actions} discrete, sequential actions. "
        "Each action must be:\n"
        "  • Concrete and specific — not vague directions\n"
        "  • Independently executable — one clear operation\n"
        "  • Realistic for the domain\n\n"
        "Include a realistic mix of action types:\n"
        "  • 2-3 routine read/query actions (low risk)\n"
        "  • 1-2 write/modify actions (medium risk)\n"
        "  • 1-2 high-impact or irreversible actions (high risk)\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "task_summary": "one sentence describing the overall task",\n'
        '  "actions": [\n'
        '    {\n'
        '      "index": 1,\n'
        '      "action": "precise action description",\n'
        '      "type": "read|write|execute|communicate|modify|delete",\n'
        '      "target": "specific system, dataset, person, or resource",\n'
        '      "expected_outcome": "what will happen if this action executes"\n'
        '    }\n'
        "  ]\n"
        "}"
    )

    raw  = generate_response(prompt)
    data = _extract_json(raw)

    actions = data.get("actions", [])

    if not actions:
        # Fallback: generic actions
        actions = [
            {
                "index": i + 1,
                "action": f"Step {i + 1}: {task}",
                "type": "execute",
                "target": "system",
                "expected_outcome": "Task step completed",
            }
            for i in range(num_actions)
        ]

    return {
        "task_summary": data.get("task_summary", task[:100]),
        "domain":       domain,
        "actions":      actions[:num_actions],
    }
