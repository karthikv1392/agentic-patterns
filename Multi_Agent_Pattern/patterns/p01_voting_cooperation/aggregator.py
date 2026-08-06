"""Aggregator — collects all agent votes and produces a final decision.

Three aggregation modes
-----------------------
1. majority   — An LLM extracts the core position from each response, then
                finds the most commonly shared stance and explains it.

2. weighted   — Each agent has a predefined weight.  A scoring LLM rates
                every response 1-10 on quality/relevance.  The response with
                the highest weighted score wins and is used as the final answer.

3. llm        — A meta-LLM reads all responses side-by-side and freely picks
                the best one, providing a detailed rationale.
"""

import json
import re

from shared.llm import generate_response

# Predefined weights per agent name (must sum to 1.0).
# Adjust to shift trust toward specific agent styles.
AGENT_WEIGHTS: dict[str, float] = {
    "Conservative Agent": 0.30,
    "Creative Agent":     0.30,
    "Analytical Agent":   0.40,
}
DEFAULT_WEIGHT = 0.33


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of an LLM response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def _format_votes_block(votes: list[dict]) -> str:
    """Render votes as a readable numbered block for LLM prompts."""
    lines = []
    for i, v in enumerate(votes, 1):
        lines.append(f"--- Agent {i}: {v['agent_name']} (model: {v['model']}) ---")
        lines.append(v["response"])
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Aggregation modes
# ---------------------------------------------------------------------------

def _aggregate_majority(votes: list[dict]) -> dict:
    """Majority-vote aggregation.

    Asks an LLM to:
      1. Extract a one-sentence core position from each response.
      2. Identify the most commonly shared position.
      3. Synthesise a final answer representing that majority view.
    """
    votes_block = _format_votes_block(votes)

    prompt = (
        "You are an impartial judge evaluating responses from multiple AI agents "
        "that were all given the same task.\n\n"
        "AGENT RESPONSES:\n"
        f"{votes_block}\n"
        "INSTRUCTIONS:\n"
        "1. For each agent, extract a one-sentence summary of its core position.\n"
        "2. Identify which position (or closely related positions) appears most often — "
        "this is the majority view.\n"
        "3. Write a final, comprehensive answer that represents the majority consensus.\n\n"
        "Return ONLY valid JSON in exactly this structure:\n"
        "{\n"
        '  "core_positions": [\n'
        '    {"agent_name": "...", "position": "one-sentence summary"},\n'
        "    ...\n"
        "  ],\n"
        '  "majority_position": "description of the winning stance",\n'
        '  "final_answer": "the full synthesised answer (markdown OK)",\n'
        '  "reasoning": "why this is the majority view"\n'
        "}"
    )

    raw = generate_response(prompt)
    data = _extract_json(raw)

    return {
        "mode": "majority",
        "core_positions": data.get("core_positions", []),
        "winning_agent": "Majority consensus",
        "majority_position": data.get("majority_position", ""),
        "final_answer": data.get("final_answer", raw),
        "reasoning": data.get("reasoning", ""),
        "scores": {},
    }


def _aggregate_weighted(votes: list[dict]) -> dict:
    """Weighted-score aggregation.

    An LLM scores each response 1-10 on quality and relevance.
    The final weighted score = predefined_weight × llm_score.
    The highest-scoring response becomes the final answer, optionally
    enriched with a brief synthesis note.
    """
    votes_block = _format_votes_block(votes)

    # Ask LLM to score each response
    agent_names = [v["agent_name"] for v in votes]
    names_list  = "\n".join(f"- {n}" for n in agent_names)

    scoring_prompt = (
        "You are an impartial evaluator. Score each agent response below on a "
        "scale of 1-10 based on accuracy, depth, clarity, and usefulness.\n\n"
        "AGENT RESPONSES:\n"
        f"{votes_block}\n"
        "AGENTS TO SCORE:\n"
        f"{names_list}\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "scores": [\n'
        '    {"agent_name": "...", "score": <1-10>, "rationale": "one sentence"},\n'
        "    ...\n"
        "  ]\n"
        "}"
    )

    raw_scores = generate_response(scoring_prompt)
    scores_data = _extract_json(raw_scores)
    llm_scores: dict[str, float] = {}
    score_rationales: dict[str, str] = {}
    for entry in scores_data.get("scores", []):
        name = entry.get("agent_name", "")
        llm_scores[name] = float(entry.get("score", 5))
        score_rationales[name] = entry.get("rationale", "")

    # Compute weighted scores
    weighted: dict[str, float] = {}
    for v in votes:
        n = v["agent_name"]
        w = AGENT_WEIGHTS.get(n, DEFAULT_WEIGHT)
        s = llm_scores.get(n, 5.0)
        weighted[n] = round(w * s, 3)

    winner_name = max(weighted, key=lambda k: weighted[k])
    winner_vote = next(v for v in votes if v["agent_name"] == winner_name)

    scores_detail = [
        {
            "agent_name": v["agent_name"],
            "weight": AGENT_WEIGHTS.get(v["agent_name"], DEFAULT_WEIGHT),
            "llm_score": llm_scores.get(v["agent_name"], 5.0),
            "weighted_score": weighted.get(v["agent_name"], 0.0),
            "rationale": score_rationales.get(v["agent_name"], ""),
        }
        for v in votes
    ]

    return {
        "mode": "weighted",
        "scores": scores_detail,
        "winning_agent": winner_name,
        "final_answer": winner_vote["response"],
        "reasoning": (
            f"{winner_name} achieved the highest weighted score "
            f"({weighted[winner_name]:.3f} = weight {AGENT_WEIGHTS.get(winner_name, DEFAULT_WEIGHT)} "
            f"× LLM score {llm_scores.get(winner_name, 5.0):.1f}/10)."
        ),
        "core_positions": [],
        "majority_position": "",
    }


def _aggregate_llm(votes: list[dict]) -> dict:
    """LLM-based free selection.

    A meta-LLM reads all responses and freely decides which is best,
    explaining its reasoning in detail.
    """
    votes_block = _format_votes_block(votes)
    agent_names = [v["agent_name"] for v in votes]

    prompt = (
        "You are a senior expert judge evaluating multiple AI agent responses "
        "to the same task. Read each response carefully.\n\n"
        "AGENT RESPONSES:\n"
        f"{votes_block}\n"
        "INSTRUCTIONS:\n"
        "Choose the single best response. Consider: accuracy, completeness, "
        "clarity, practical usefulness, and depth of reasoning.\n"
        "You may also synthesise insights from multiple responses into an "
        "improved final answer.\n\n"
        f"Available agent names: {agent_names}\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "winning_agent": "exact agent name from the list",\n'
        '  "final_answer": "your best answer (may synthesise across agents, markdown OK)",\n'
        '  "reasoning": "detailed explanation of why this is the best choice and what you kept/discarded"\n'
        "}"
    )

    raw = generate_response(prompt)
    data = _extract_json(raw)

    return {
        "mode": "llm",
        "winning_agent": data.get("winning_agent", "LLM Aggregator"),
        "final_answer": data.get("final_answer", raw),
        "reasoning": data.get("reasoning", ""),
        "scores": [],
        "core_positions": [],
        "majority_position": "",
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def aggregate(votes: list[dict], mode: str = "llm") -> dict:
    """Aggregate a list of agent votes into a final decision.

    Parameters
    ----------
    votes : list of dicts from BaseAgent.vote()
            Each dict: {"agent_name", "model", "response"}
    mode  : "majority" | "weighted" | "llm"

    Returns
    -------
    dict with keys:
        mode, winning_agent, final_answer, reasoning,
        scores (weighted mode), core_positions / majority_position (majority mode)
    """
    if not votes:
        raise ValueError("Cannot aggregate zero votes.")

    mode = mode.lower()
    if mode == "majority":
        return _aggregate_majority(votes)
    if mode == "weighted":
        return _aggregate_weighted(votes)
    if mode == "llm":
        return _aggregate_llm(votes)

    raise ValueError(f"Unknown aggregation mode: {mode!r}. Choose majority | weighted | llm.")
