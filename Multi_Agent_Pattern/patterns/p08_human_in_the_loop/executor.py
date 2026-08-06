"""Executor — simulates domain-realistic action execution.

Each action carries an approval decision. The executor:
  • Auto-runs LOW and MEDIUM actions (no human gate needed).
  • Runs HIGH actions only when approval_status == "approved".
  • Skips HIGH actions that were rejected.
  • Produces a realistic simulated outcome per domain via LLM.
"""

import json
import re
from datetime import datetime, timezone

from shared.llm import generate_response


_DOMAIN_EXECUTION_CONTEXT = {
    "Clinical": (
        "You are simulating the execution of an action in a clinical healthcare system. "
        "Describe the realistic outcome in 2-3 sentences as if the system executed it. "
        "Include relevant clinical details (patient IDs, order numbers, timestamps)."
    ),
    "Trading": (
        "You are simulating the execution of an action in a financial trading platform. "
        "Describe the realistic outcome in 2-3 sentences as if the system executed it. "
        "Include relevant trading details (order IDs, ticker symbols, fill prices, timestamps)."
    ),
    "DevOps": (
        "You are simulating the execution of an action in a production infrastructure environment. "
        "Describe the realistic outcome in 2-3 sentences as if the system executed it. "
        "Include relevant DevOps details (service names, deployment IDs, metrics, timestamps)."
    ),
    "Custom": (
        "You are simulating the execution of an action in a general enterprise system. "
        "Describe the realistic outcome in 2-3 sentences as if the system executed it. "
        "Include relevant operational details."
    ),
}


def _simulate_execution(action: dict, domain: str) -> str:
    """Use LLM to produce a realistic execution outcome string."""
    ctx = _DOMAIN_EXECUTION_CONTEXT.get(domain, _DOMAIN_EXECUTION_CONTEXT["Custom"])
    prompt = (
        f"{ctx}\n\n"
        f"Action  : {action['action']}\n"
        f"Type    : {action['type']}\n"
        f"Target  : {action['target']}\n"
        f"Expected: {action['expected_outcome']}\n\n"
        "Generate the execution outcome (2-3 sentences, past tense, specific details). "
        "Do NOT include any JSON — plain text only."
    )
    return generate_response(prompt).strip()


def execute_actions(
    domain: str,
    classified_actions: list,
    approvals: dict,
) -> list:
    """Execute each action according to its risk level and approval decision.

    Parameters
    ----------
    domain             : Domain context string.
    classified_actions : List of action dicts enriched with risk classification fields.
    approvals          : {action_index: {"status": "approved"|"rejected", "approver": str,
                          "notes": str, "timestamp": str}}
                          Only HIGH-risk actions have entries here.

    Returns
    -------
    List of execution result dicts:
    {
        "index"            : int
        "action"           : str
        "risk_level"       : str
        "executed"         : bool
        "skip_reason"      : str | None
        "approval_status"  : "auto_approved" | "human_approved" | "rejected" | "not_required"
        "outcome"          : str
        "executed_at"      : str (ISO-8601 UTC)
        "approver"         : str | None
        "approver_notes"   : str | None
    }
    """
    results = []

    for ca in classified_actions:
        idx        = ca["index"]
        risk_level = ca["risk_level"]
        now_iso    = datetime.now(timezone.utc).isoformat()

        # ── Determine whether to execute ────────────────────────────────────
        if risk_level in ("low", "medium"):
            executed        = True
            skip_reason     = None
            approval_status = "auto_approved"
            approver        = "system"
            approver_notes  = "Auto-approved: risk level does not require human review."
            outcome         = _simulate_execution(ca, domain)

        else:  # high risk — check approval dict
            approval = approvals.get(idx) or approvals.get(str(idx))

            if approval is None:
                # Treat missing approval as pending/rejected for safety
                executed        = False
                skip_reason     = "No approval decision recorded — skipped for safety."
                approval_status = "rejected"
                approver        = None
                approver_notes  = None
                outcome         = "Action was not executed (no approval received)."

            elif approval["status"] == "approved":
                executed        = True
                skip_reason     = None
                approval_status = "human_approved"
                approver        = approval.get("approver", "unknown")
                approver_notes  = approval.get("notes", "")
                outcome         = _simulate_execution(ca, domain)

            else:  # rejected
                executed        = False
                skip_reason     = f"Rejected by {approval.get('approver', 'unknown')}."
                approval_status = "rejected"
                approver        = approval.get("approver", "unknown")
                approver_notes  = approval.get("notes", "")
                outcome         = "Action was not executed (rejected by human reviewer)."

        results.append(
            {
                "index":           idx,
                "action":          ca["action"],
                "risk_level":      risk_level,
                "executed":        executed,
                "skip_reason":     skip_reason,
                "approval_status": approval_status,
                "outcome":         outcome,
                "executed_at":     now_iso,
                "approver":        approver,
                "approver_notes":  approver_notes,
            }
        )

    return results
