"""Synthesizer — integrates outputs from all spawned sub-agents.

Unlike a generic merge/summarise/vote synthesizer, this one is context-aware:
it receives the Spawner's synthesis_hint and uses it to integrate outputs in
a way that makes sense for the specific task and domain (e.g., for code
migration it reassembles code by module; for system design it builds a
coherent architecture document).
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


def _format_results_block(results: list[dict]) -> str:
    lines = []
    for r in results:
        lines.append(
            f"=== {r['name']} | Role: {r['role']} | Focus: {r['focus_area']} ==="
        )
        lines.append(r["output"])
        lines.append("")
    return "\n".join(lines)


def synthesize(
    task: str,
    domain: str,
    strategy: str,
    results: list[dict],
    synthesis_hint: str,
) -> dict:
    """Integrate all sub-agent outputs into a coherent final output.

    Parameters
    ----------
    task            : Original task.
    domain          : Task domain (Code Migration, System Design, etc.).
    strategy        : Decomposition strategy used by the Spawner.
    results         : List of sub-agent execution result dicts.
    synthesis_hint  : Spawner's guidance on how to integrate outputs.

    Returns
    -------
    {
        "final_output"        : str,   — the integrated result
        "integration_notes"   : str,   — how outputs were combined
        "key_contributions"   : list,  — [{"agent": str, "contribution": str}]
    }
    """
    if not results:
        return {
            "final_output":      "No sub-agent outputs to synthesize.",
            "integration_notes": "",
            "key_contributions": [],
        }

    block = _format_results_block(results)
    agent_names = [r["name"] for r in results]

    prompt = (
        "You are a senior integrator synthesizing outputs from multiple specialist sub-agents "
        f"who executed in parallel on a {domain} task.\n\n"
        f"Original task:\n{task}\n\n"
        f"Decomposition strategy used:\n{strategy}\n\n"
        f"Integration guidance from the Spawner:\n{synthesis_hint}\n\n"
        f"Sub-agent outputs:\n{block}\n"
        "Produce a coherent, complete integrated result that:\n"
        "  1. Combines all sub-agent outputs without losing important details.\n"
        "  2. Resolves any inconsistencies between agents.\n"
        "  3. Maintains the structure appropriate for the domain "
        "(code files for Code Migration, architecture doc for System Design, etc.).\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "final_output": "the full integrated result in markdown",\n'
        '  "integration_notes": "2-3 sentences on how outputs were combined",\n'
        '  "key_contributions": [\n'
        '    {"agent": "agent name", "contribution": "one-sentence summary of their key contribution"},\n'
        "    ...\n"
        "  ]\n"
        "}"
    )

    raw = generate_response(prompt)
    data = _extract_json(raw)

    if not data.get("final_output"):
        # Fallback: concatenate outputs
        data = {
            "final_output": block,
            "integration_notes": "Concatenated sub-agent outputs (parsing fallback).",
            "key_contributions": [
                {"agent": r["name"], "contribution": r["focus_area"]}
                for r in results
            ],
        }

    return {
        "final_output":      data.get("final_output", block),
        "integration_notes": data.get("integration_notes", ""),
        "key_contributions": data.get("key_contributions", []),
    }
