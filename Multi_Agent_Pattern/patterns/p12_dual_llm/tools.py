"""Simulated tool registry for the Privileged LLM.

These are the ONLY tools the Privileged LLM can call.  It NEVER sees raw user
data — it receives only the validated, substituted parameter primitives that
survived the quarantine + substitution pipeline.
"""

from datetime import datetime

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

AVAILABLE_TOOLS: dict[str, dict] = {
    "send_email": {
        "description": "Send an email to a recipient.",
        "required_params": ["to", "subject", "body"],
        "icon": "📧",
    },
    "schedule_meeting": {
        "description": "Schedule a calendar meeting with attendees.",
        "required_params": ["attendees", "title", "time"],
        "icon": "📅",
    },
    "create_task": {
        "description": "Create a task in the project management system.",
        "required_params": ["title", "assignee", "due_date"],
        "icon": "✅",
    },
    "post_message": {
        "description": "Post a message to a Slack channel.",
        "required_params": ["channel", "message"],
        "icon": "💬",
    },
}


def simulate_tool(tool_name: str, params: dict) -> dict:
    """Simulate executing a tool and return a mock result.

    In a real system this would call the actual API.  Here we return a
    deterministic success confirmation so the demo works end-to-end.
    """
    if tool_name not in AVAILABLE_TOOLS:
        return {
            "success": False,
            "tool":    tool_name,
            "error":   f"Unknown tool: {tool_name!r}",
            "result":  None,
        }

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    mock_results = {
        "send_email": (
            f"Email delivered at {ts}. "
            f"Recipient: {params.get('to', '?')} | "
            f"Subject: {params.get('subject', '?')!r}. "
            "Message ID: msg_" + hex(hash(str(params)) & 0xFFFFFF)[2:]
        ),
        "schedule_meeting": (
            f"Meeting created at {ts}. "
            f"Title: {params.get('title', '?')!r} | "
            f"Time: {params.get('time', '?')} | "
            f"Attendees: {params.get('attendees', '?')}. "
            "Event ID: evt_" + hex(hash(str(params)) & 0xFFFFFF)[2:]
        ),
        "create_task": (
            f"Task created at {ts}. "
            f"Title: {params.get('title', '?')!r} | "
            f"Assignee: {params.get('assignee', '?')} | "
            f"Due: {params.get('due_date', '?')}. "
            "Task ID: tsk_" + hex(hash(str(params)) & 0xFFFFFF)[2:]
        ),
        "post_message": (
            f"Message posted at {ts}. "
            f"Channel: #{params.get('channel', '?')} | "
            f"Preview: {str(params.get('message', ''))[:60]}… "
            "Message ID: msg_" + hex(hash(str(params)) & 0xFFFFFF)[2:]
        ),
    }

    return {
        "success": True,
        "tool":    tool_name,
        "params":  params,
        "result":  mock_results[tool_name],
        "ts":      ts,
    }
