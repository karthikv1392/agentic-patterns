"""Incremental Tool Agent — single-agent pattern demo.

The agent queries the LLM multiple times in sequence. Each round receives the
original goal PLUS all previous round responses as context, progressively
refining its understanding until it produces a precise tool call in the final
round. Tools are then executed and the results synthesised into a final answer.

Rounds:
    Round 1  — Goal analysis: what is needed to solve this?
    Round 2  — Goal + R1 → Action plan + tool selection (which tool & why)
    Round 3  — Goal + R1 + R2 → Precise tool parameters (JSON)
    Execution — Run the selected tool with the specified parameters
    Synthesis — LLM combines all context + tool output → final answer

Flow:
    Goal → R1 → [Goal+R1] → R2 → [Goal+R1+R2] → R3 (JSON) → Tool → Synthesis
"""

import json
import re

from tools import TOOL_REGISTRY, execute_tool, tool_descriptions_text
from utils import generate_response


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of an LLM response."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"No JSON object found in LLM response:\n{text[:400]}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_incremental_tool_agent(user_goal: str) -> dict:
    """Run the incremental tool-agent pipeline.

    Steps:
        Round 1 — Analyse the goal and identify what information/capabilities
                  are needed.
        Round 2 — Given R1 analysis, produce a concrete action plan and choose
                  the best tool.
        Round 3 — Given R1 + R2, specify exact tool parameters as JSON.
        Execute  — Run the chosen tool.
        Synthesise — Produce the final answer grounded in all context.

    Returns a dict with keys:
        rounds          — list of dicts, each with 'round', 'prompt', 'response'
        selected_tool   — tool chosen in Round 3
        tool_parameters — parameters chosen in Round 3
        tool_output     — raw string output from the tool
        final_output    — final synthesised LLM response
    """

    rounds: list[dict] = []

    # ------------------------------------------------------------------
    # Round 1 — Goal analysis
    # ------------------------------------------------------------------
    r1_prompt = (
        "You are an expert AI agent. A user has given you this goal:\n\n"
        f'"{user_goal}"\n\n'
        "Step 1 — Analysis:\n"
        "Carefully analyse the goal. Identify:\n"
        "- The core objective the user wants to achieve.\n"
        "- Any implicit constraints or requirements.\n"
        "- What information or capabilities will be needed to solve it.\n"
        "- Potential challenges or ambiguities.\n\n"
        "Write your analysis in plain, structured prose. Do NOT propose "
        "solutions yet — focus entirely on understanding the problem."
    )
    r1_response = generate_response(r1_prompt)
    rounds.append({"round": 1, "label": "Goal Analysis", "prompt": r1_prompt, "response": r1_response})

    # ------------------------------------------------------------------
    # Round 2 — Action plan + tool selection
    # ------------------------------------------------------------------
    r2_prompt = (
        "You are an expert AI agent working on this goal:\n\n"
        f'"{user_goal}"\n\n'
        "=== Round 1 Analysis ===\n"
        f"{r1_response}\n"
        "=== End Round 1 ===\n\n"
        "Step 2 — Action Plan & Tool Selection:\n"
        "Given your Round 1 analysis, now:\n"
        "1. Write a numbered action plan (3–5 steps) to accomplish the goal.\n"
        "2. Review the available tools below and select the single most useful one:\n\n"
        f"{tool_descriptions_text()}\n\n"
        "3. Explain clearly why that tool is the best choice for this goal.\n\n"
        "Do NOT specify exact parameters yet — that comes in the next round."
    )
    r2_response = generate_response(r2_prompt)
    rounds.append({"round": 2, "label": "Action Plan & Tool Selection", "prompt": r2_prompt, "response": r2_response})

    # ------------------------------------------------------------------
    # Round 3 — Precise tool parameters (JSON)
    # ------------------------------------------------------------------
    r3_prompt = (
        "You are an expert AI agent working on this goal:\n\n"
        f'"{user_goal}"\n\n'
        "=== Round 1 Analysis ===\n"
        f"{r1_response}\n"
        "=== End Round 1 ===\n\n"
        "=== Round 2 Action Plan & Tool Selection ===\n"
        f"{r2_response}\n"
        "=== End Round 2 ===\n\n"
        "Step 3 — Finalise Tool Call:\n"
        "Based on Rounds 1 and 2, produce the exact tool invocation. "
        "Respond with a single JSON object and nothing else:\n\n"
        "```json\n"
        "{\n"
        '  "selected_tool": "<exact tool name>",\n'
        '  "parameters": {<all required parameters as key-value pairs>}\n'
        "}\n"
        "```"
    )
    r3_response = generate_response(r3_prompt)
    rounds.append({"round": 3, "label": "Precise Tool Parameters", "prompt": r3_prompt, "response": r3_response})

    # ------------------------------------------------------------------
    # Parse Round 3 → extract tool name + parameters
    # ------------------------------------------------------------------
    try:
        tool_spec = _extract_json(r3_response)
        selected_tool = tool_spec.get("selected_tool", "none")
        tool_parameters = tool_spec.get("parameters", {})
    except (ValueError, json.JSONDecodeError):
        # Fallback: try to parse from Round 2 text
        selected_tool = "none"
        tool_parameters = {}

    # ------------------------------------------------------------------
    # Execute the tool
    # ------------------------------------------------------------------
    if selected_tool in TOOL_REGISTRY:
        tool_output = execute_tool(selected_tool, tool_parameters)
    else:
        tool_output = f"Tool '{selected_tool}' not found; skipping execution."

    # ------------------------------------------------------------------
    # Final synthesis — all context + tool output → final answer
    # ------------------------------------------------------------------
    synthesis_prompt = (
        "You are an expert assistant. A user asked:\n\n"
        f'"{user_goal}"\n\n'
        "You reasoned through the problem across three rounds:\n\n"
        f"**Round 1 — Analysis:**\n{r1_response}\n\n"
        f"**Round 2 — Action Plan & Tool Selection:**\n{r2_response}\n\n"
        f"You then executed the tool **{selected_tool}** "
        f"with parameters `{json.dumps(tool_parameters)}` and received:\n"
        f"```\n{tool_output}\n```\n\n"
        "Now produce a comprehensive, well-structured final answer that fully "
        "addresses the user's goal. Incorporate all reasoning and the tool "
        "result naturally. Use markdown formatting."
    )
    final_output = generate_response(synthesis_prompt)

    return {
        "rounds": rounds,
        "selected_tool": selected_tool,
        "tool_parameters": tool_parameters,
        "tool_output": tool_output,
        "final_output": final_output,
    }


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    default_goal = "What is the concept of RAG in AI and what tools or patterns does it typically involve?"
    print(f"Running Incremental Tool Agent with goal:\n  {default_goal!r}\n")

    result = run_incremental_tool_agent(default_goal)

    for r in result["rounds"]:
        print("=" * 60)
        print(f"ROUND {r['round']} — {r['label']}")
        print("=" * 60)
        print(r["response"])
        print()

    print("=" * 60)
    print(f"SELECTED TOOL: {result['selected_tool']}")
    print(f"PARAMETERS: {result['tool_parameters']}")
    print("=" * 60)
    print()
    print("=" * 60)
    print("TOOL OUTPUT")
    print("=" * 60)
    print(result["tool_output"])
    print()
    print("=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(result["final_output"])
