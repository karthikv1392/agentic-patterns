"""Audit Trail — immutable log of every approval, rejection, and execution.

Provides:
  AuditEntry  — single log record
  AuditTrail  — append-only ledger with query helpers
  build_audit_trail() — builds the final audit trail from execution results
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AuditEntry:
    """A single immutable audit record."""
    seq:              int            # monotonic sequence number (1-based)
    action_index:     int            # which action this refers to
    action_desc:      str            # human-readable action
    risk_level:       str            # low | medium | high
    risk_score:       int
    event_type:       str            # planned | notified | approved | rejected | executed | skipped
    actor:            str            # "system" | approver name
    timestamp:        str            # ISO-8601 UTC
    notes:            Optional[str]  = None
    outcome:          Optional[str]  = None

    def to_dict(self) -> dict:
        return asdict(self)


class AuditTrail:
    """Append-only ledger of AuditEntry records."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _next_seq(self) -> int:
        return len(self._entries) + 1

    # ── Write helpers ────────────────────────────────────────────────────────

    def log_planned(self, action: dict, risk: dict) -> None:
        self._entries.append(
            AuditEntry(
                seq=self._next_seq(),
                action_index=action["index"],
                action_desc=action["action"],
                risk_level=risk["risk_level"],
                risk_score=risk["risk_score"],
                event_type="planned",
                actor="system",
                timestamp=self._now(),
                notes=f"Reversibility: {risk['reversibility']} | Scope: {risk['impact_scope']}",
            )
        )

    def log_notified(self, action: dict, risk: dict, channels: list) -> None:
        self._entries.append(
            AuditEntry(
                seq=self._next_seq(),
                action_index=action["index"],
                action_desc=action["action"],
                risk_level=risk["risk_level"],
                risk_score=risk["risk_score"],
                event_type="notified",
                actor="system",
                timestamp=self._now(),
                notes=f"Notification sent via: {', '.join(channels)}",
            )
        )

    def log_approved(self, action: dict, risk: dict, approver: str, notes: str = "") -> None:
        self._entries.append(
            AuditEntry(
                seq=self._next_seq(),
                action_index=action["index"],
                action_desc=action["action"],
                risk_level=risk["risk_level"],
                risk_score=risk["risk_score"],
                event_type="approved",
                actor=approver,
                timestamp=self._now(),
                notes=notes or "Approved by human reviewer.",
            )
        )

    def log_rejected(self, action: dict, risk: dict, approver: str, notes: str = "") -> None:
        self._entries.append(
            AuditEntry(
                seq=self._next_seq(),
                action_index=action["index"],
                action_desc=action["action"],
                risk_level=risk["risk_level"],
                risk_score=risk["risk_score"],
                event_type="rejected",
                actor=approver,
                timestamp=self._now(),
                notes=notes or "Rejected by human reviewer.",
            )
        )

    def log_executed(self, result: dict) -> None:
        self._entries.append(
            AuditEntry(
                seq=self._next_seq(),
                action_index=result["index"],
                action_desc=result["action"],
                risk_level=result["risk_level"],
                risk_score=0,
                event_type="executed",
                actor=result.get("approver", "system") or "system",
                timestamp=result.get("executed_at", self._now()),
                notes=result.get("approver_notes"),
                outcome=result["outcome"],
            )
        )

    def log_skipped(self, result: dict) -> None:
        self._entries.append(
            AuditEntry(
                seq=self._next_seq(),
                action_index=result["index"],
                action_desc=result["action"],
                risk_level=result["risk_level"],
                risk_score=0,
                event_type="skipped",
                actor=result.get("approver", "system") or "system",
                timestamp=result.get("executed_at", self._now()),
                notes=result.get("skip_reason"),
            )
        )

    # ── Read helpers ─────────────────────────────────────────────────────────

    def all_entries(self) -> list[dict]:
        return [e.to_dict() for e in self._entries]

    def entries_for_action(self, action_index: int) -> list[dict]:
        return [e.to_dict() for e in self._entries if e.action_index == action_index]

    def summary(self) -> dict:
        total    = len(self._entries)
        executed = sum(1 for e in self._entries if e.event_type == "executed")
        skipped  = sum(1 for e in self._entries if e.event_type == "skipped")
        approved = sum(1 for e in self._entries if e.event_type == "approved")
        rejected = sum(1 for e in self._entries if e.event_type == "rejected")
        return {
            "total_events":    total,
            "actions_executed": executed,
            "actions_skipped":  skipped,
            "human_approvals":  approved,
            "human_rejections": rejected,
        }


# ── Convenience builder ──────────────────────────────────────────────────────

def build_audit_trail(
    classified_actions: list,
    approvals: dict,
    execution_results: list,
) -> AuditTrail:
    """Construct a complete AuditTrail from classified actions and execution results.

    Parameters
    ----------
    classified_actions : Actions enriched with risk fields.
    approvals          : Human approval decisions keyed by action index.
    execution_results  : Output from executor.execute_actions().
    """
    trail = AuditTrail()

    # Build a quick lookup for risk info from classified actions
    risk_by_idx = {ca["index"]: ca for ca in classified_actions}

    # Log planned events
    for ca in classified_actions:
        trail.log_planned(ca, ca)

    # Log notifications (for high-risk actions)
    for ca in classified_actions:
        if ca["risk_level"] == "high" and ca.get("notification_channels"):
            trail.log_notified(ca, ca, ca["notification_channels"])

    # Log approval/rejection events
    for action_idx_raw, decision in approvals.items():
        idx = int(action_idx_raw)
        ca  = risk_by_idx.get(idx)
        if ca is None:
            continue
        if decision["status"] == "approved":
            trail.log_approved(ca, ca, decision.get("approver", "unknown"), decision.get("notes", ""))
        else:
            trail.log_rejected(ca, ca, decision.get("approver", "unknown"), decision.get("notes", ""))

    # Log execution / skip events
    for result in execution_results:
        if result["executed"]:
            trail.log_executed(result)
        else:
            trail.log_skipped(result)

    return trail
