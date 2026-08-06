"""Risk Classifier — evaluates each action and assigns a risk level.

Risk levels
-----------
LOW    (score 1-3)  : Read-only, fully reversible, no external effects.
                      Auto-approved; no human review needed.

MEDIUM (score 4-6)  : Write to non-critical systems, reversible within
                      a short window, limited blast radius.
                      Auto-approved but flagged for awareness.

HIGH   (score 7-10) : Irreversible, large blast radius, financial impact,
                      patient-critical, regulatory exposure, or external
                      communication. Requires explicit human approval.

Classification criteria
-----------------------
  • Reversibility  — can this be undone in < 5 minutes?
  • Impact scope   — local | team | system-wide | external
  • Data sensitivity — does it touch PII, PHI, financial, or secret data?
  • Financial impact — any monetary transaction or risk exposure?
  • Regulatory      — HIPAA / SOX / SEC / GDPR exposure?
  • Recovery time   — if this goes wrong, how long to recover?
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


_DOMAIN_RISK_CONTEXT = {
    "Clinical": (
        "Patient safety is paramount. Any action that administers treatment, "
        "modifies a medication order, or changes a care plan is HIGH risk. "
        "Reading patient records is LOW-MEDIUM depending on sensitivity."
    ),
    "Trading": (
        "Any action that moves money, places orders above $10k, or modifies "
        "risk limits is HIGH risk. Market data reads and small rebalances are LOW-MEDIUM."
    ),
    "DevOps": (
        "Any action on production infrastructure, secret rotation, or firewall "
        "changes is HIGH risk. Staging deployments and log reads are LOW-MEDIUM."
    ),
    "Custom": (
        "Evaluate based on reversibility, scope, and sensitivity of data involved."
    ),
}


def classify_action(action: dict, domain: str, task_context: str) -> dict:
    """Classify the risk level of a single action.

    Parameters
    ----------
    action       : Action dict from action_planner (index, action, type, target, expected_outcome).
    domain       : Domain context string.
    task_context : The original task for additional context.

    Returns
    -------
    {
        "risk_level"      : "low" | "medium" | "high"
        "risk_score"      : int (1-10)
        "reversibility"   : str  — human-readable reversibility assessment
        "impact_scope"    : str  — who / what is affected
        "data_sensitivity": str  — type of data involved
        "reasoning"       : str  — why this risk level was assigned
        "approval_required": bool
        "notification_channels": list[str]  — ["slack", "email"] for high risk
    }
    """
    domain_ctx = _DOMAIN_RISK_CONTEXT.get(domain, _DOMAIN_RISK_CONTEXT["Custom"])

    prompt = (
        f"You are a risk assessment specialist for a {domain} system.\n\n"
        f"Domain risk context:\n{domain_ctx}\n\n"
        f"Overall task: {task_context}\n\n"
        "Evaluate the following action:\n"
        f"  Action : {action['action']}\n"
        f"  Type   : {action['type']}\n"
        f"  Target : {action['target']}\n"
        f"  Outcome: {action['expected_outcome']}\n\n"
        "Assess the risk across these dimensions:\n"
        "  • Reversibility (can this be undone quickly?)\n"
        "  • Impact scope (local / team / system-wide / external)\n"
        "  • Data sensitivity (public / internal / confidential / regulated)\n"
        "  • Financial / regulatory exposure\n\n"
        "Assign a risk score 1-10 and map to level:\n"
        "  1-3 = low, 4-6 = medium, 7-10 = high\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "risk_score": <1-10>,\n'
        '  "risk_level": "low|medium|high",\n'
        '  "reversibility": "easily reversible|reversible within window|hard to reverse|irreversible",\n'
        '  "impact_scope": "local|team-wide|system-wide|external",\n'
        '  "data_sensitivity": "public|internal|confidential|regulated (PHI/PII/PCI)",\n'
        '  "reasoning": "2-3 sentences explaining the risk assessment",\n'
        '  "approval_required": true|false,\n'
        '  "notification_channels": ["slack", "email"]\n'
        "}"
    )

    raw  = generate_response(prompt)
    data = _extract_json(raw)

    risk_score = int(data.get("risk_score", 5))
    risk_score = max(1, min(10, risk_score))

    # Derive level from score if LLM inconsistency
    if risk_score <= 3:
        risk_level = "low"
    elif risk_score <= 6:
        risk_level = "medium"
    else:
        risk_level = "high"

    approval_required = risk_level == "high"
    channels = ["slack", "email"] if approval_required else []

    return {
        "risk_score":            risk_score,
        "risk_level":            risk_level,
        "reversibility":         data.get("reversibility", "unknown"),
        "impact_scope":          data.get("impact_scope", "unknown"),
        "data_sensitivity":      data.get("data_sensitivity", "internal"),
        "reasoning":             data.get("reasoning", "Risk assessment completed."),
        "approval_required":     approval_required,
        "notification_channels": channels if approval_required else [],
    }
