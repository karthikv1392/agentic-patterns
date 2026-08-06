"""Notifier — formats simulated Slack and email approval request cards.

No LLM is used here; notifications are deterministic templates so they
render instantly in the UI and look realistic without incurring latency.
"""

from datetime import datetime, timezone


# ── Slack-style card ────────────────────────────────────────────────────────

def build_slack_notification(action: dict, risk: dict, domain: str, task_summary: str) -> dict:
    """Build a Slack Block Kit-style notification card (as a dict).

    The dict is used by app.py to render a styled card in the UI.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    risk_emoji = {
        "high":   "🔴",
        "medium": "🟡",
        "low":    "🟢",
    }.get(risk["risk_level"], "⚪")

    domain_emoji = {
        "Clinical": "🏥",
        "Trading":  "📈",
        "DevOps":   "⚙️",
        "Custom":   "🏢",
    }.get(domain, "🏢")

    return {
        "channel":   f"#{domain.lower()}-approvals",
        "timestamp": ts,
        "blocks": [
            {
                "type": "header",
                "text": f"{risk_emoji} HIGH-RISK ACTION — Approval Required",
            },
            {
                "type": "section",
                "fields": [
                    ("Domain",     f"{domain_emoji} {domain}"),
                    ("Task",       task_summary),
                    ("Action #",   str(action["index"])),
                    ("Type",       action["type"].upper()),
                    ("Target",     action["target"]),
                    ("Risk Score", f"{risk['risk_score']} / 10"),
                ],
            },
            {
                "type": "description",
                "text": action["action"],
            },
            {
                "type": "risk_details",
                "fields": [
                    ("Reversibility",    risk["reversibility"]),
                    ("Impact Scope",     risk["impact_scope"]),
                    ("Data Sensitivity", risk["data_sensitivity"]),
                ],
            },
            {
                "type": "reasoning",
                "text": risk["reasoning"],
            },
            {
                "type": "actions",
                "buttons": ["✅ Approve", "❌ Reject"],
            },
        ],
    }


# ── Email-style card ────────────────────────────────────────────────────────

def build_email_notification(action: dict, risk: dict, domain: str, task_summary: str) -> dict:
    """Build an email-style approval request (as a dict).

    The dict is used by app.py to render a styled email card in the UI.
    """
    ts  = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    domain_team = {
        "Clinical": "Chief Medical Officer / Clinical Compliance",
        "Trading":  "Head of Trading / Risk Management",
        "DevOps":   "VP Engineering / Site Reliability Lead",
        "Custom":   "Department Head / Compliance Officer",
    }.get(domain, "Department Head")

    subject = (
        f"[ACTION REQUIRED] High-Risk Agent Action — "
        f"{domain} · Action #{action['index']} · Score {risk['risk_score']}/10"
    )

    body_lines = [
        f"To: {domain_team}",
        f"Subject: {subject}",
        "",
        f"An autonomous agent is requesting approval for a HIGH-RISK action.",
        "",
        f"  Task      : {task_summary}",
        f"  Action    : {action['action']}",
        f"  Type      : {action['type'].upper()}",
        f"  Target    : {action['target']}",
        f"  Expected  : {action['expected_outcome']}",
        "",
        "Risk Assessment",
        "───────────────",
        f"  Score         : {risk['risk_score']} / 10  (HIGH)",
        f"  Reversibility : {risk['reversibility']}",
        f"  Impact Scope  : {risk['impact_scope']}",
        f"  Data Sensitivity: {risk['data_sensitivity']}",
        "",
        "Reasoning",
        "─────────",
        f"  {risk['reasoning']}",
        "",
        "Please approve or reject this action in the agent console.",
        "",
        f"Generated: {ts}",
    ]

    return {
        "to":      domain_team,
        "subject": subject,
        "body":    "\n".join(body_lines),
        "sent_at": ts,
    }


# ── Convenience wrapper ─────────────────────────────────────────────────────

def build_notifications(action: dict, risk: dict, domain: str, task_summary: str) -> dict:
    """Return both Slack and email notification cards for a high-risk action."""
    return {
        "slack": build_slack_notification(action, risk, domain, task_summary),
        "email": build_email_notification(action, risk, domain, task_summary),
    }
