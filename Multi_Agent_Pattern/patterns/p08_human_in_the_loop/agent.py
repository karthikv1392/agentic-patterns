"""Human-in-the-Loop Approval — entry point.

Two-phase API
-------------
Phase 1  plan_and_classify(task, domain)
    Decomposes the task into actions, classifies each by risk level,
    and builds simulated notification cards for HIGH-risk actions.
    Returns everything the UI needs to render the approval panel.

Phase 2  execute_approved_plan(task, domain, classified_actions, approvals)
    Receives the human's approval decisions (keyed by action index),
    executes each action accordingly, and returns results + full audit trail.

Risk levels
-----------
  LOW    (1-3)  : Auto-approved, executed without human review.
  MEDIUM (4-6)  : Auto-approved but flagged for awareness.
  HIGH   (7-10) : Requires explicit human approval before execution.
"""

from patterns.p08_human_in_the_loop.action_planner  import plan_actions
from patterns.p08_human_in_the_loop.risk_classifier import classify_action
from patterns.p08_human_in_the_loop.notifier        import build_notifications
from patterns.p08_human_in_the_loop.executor        import execute_actions
from patterns.p08_human_in_the_loop.audit           import build_audit_trail


# ── Phase 1 ──────────────────────────────────────────────────────────────────

def plan_and_classify(task: str, domain: str, num_actions: int = 6) -> dict:
    """Decompose task and classify every action by risk.

    Returns
    -------
    {
        "task_summary"      : str
        "domain"            : str
        "classified_actions": [
            {
                # --- from action_planner ---
                "index"            : int
                "action"           : str
                "type"             : str
                "target"           : str
                "expected_outcome" : str
                # --- from risk_classifier ---
                "risk_score"       : int
                "risk_level"       : "low" | "medium" | "high"
                "reversibility"    : str
                "impact_scope"     : str
                "data_sensitivity" : str
                "reasoning"        : str
                "approval_required": bool
                "notification_channels": list[str]
                # --- notifications (high-risk only) ---
                "notifications"    : dict | None   # {"slack": ..., "email": ...}
            },
            ...
        ]
        "high_risk_count"   : int
        "medium_risk_count" : int
        "low_risk_count"    : int
    }
    """
    # Step 1 — decompose task into actions
    plan = plan_actions(task, domain, num_actions)
    task_summary = plan["task_summary"]

    classified_actions = []
    for action in plan["actions"]:
        # Step 2 — classify each action
        risk = classify_action(action, domain, task_summary)

        # Step 3 — build notification cards for high-risk actions
        notifications = None
        if risk["approval_required"]:
            notifications = build_notifications(action, risk, domain, task_summary)

        classified_actions.append(
            {
                **action,
                **risk,
                "notifications": notifications,
            }
        )

    counts = {"high": 0, "medium": 0, "low": 0}
    for ca in classified_actions:
        counts[ca["risk_level"]] = counts.get(ca["risk_level"], 0) + 1

    return {
        "task_summary":       task_summary,
        "domain":             domain,
        "classified_actions": classified_actions,
        "high_risk_count":    counts["high"],
        "medium_risk_count":  counts["medium"],
        "low_risk_count":     counts["low"],
    }


# ── Phase 2 ──────────────────────────────────────────────────────────────────

def execute_approved_plan(
    task: str,
    domain: str,
    classified_actions: list,
    approvals: dict,
) -> dict:
    """Execute the plan with human approval decisions applied.

    Parameters
    ----------
    task               : The original task string.
    domain             : Domain context.
    classified_actions : Output of plan_and_classify()["classified_actions"].
    approvals          : {action_index: {"status": "approved"|"rejected",
                          "approver": str, "notes": str, "timestamp": str}}
                         Only HIGH-risk actions need entries; LOW/MEDIUM are auto-approved.

    Returns
    -------
    {
        "task"             : str
        "domain"           : str
        "execution_results": list  — per-action execution outcome dicts
        "audit_trail"      : list  — full chronological audit log (list of dicts)
        "audit_summary"    : dict  — summary counts
        "actions_executed" : int
        "actions_skipped"  : int
    }
    """
    # Step 1 — execute
    results = execute_actions(domain, classified_actions, approvals)

    # Step 2 — build audit trail
    trail = build_audit_trail(classified_actions, approvals, results)

    executed = sum(1 for r in results if r["executed"])
    skipped  = sum(1 for r in results if not r["executed"])

    return {
        "task":             task,
        "domain":           domain,
        "execution_results": results,
        "audit_trail":      trail.all_entries(),
        "audit_summary":    trail.summary(),
        "actions_executed": executed,
        "actions_skipped":  skipped,
    }
