"""Generator-Critic Loop — entry point.

The Generator produces a draft; the Critic evaluates it. If it fails, the
Generator refines it using the Critic's feedback. This loop repeats until
the Critic is satisfied (passed=True) or max_iterations is reached.

Returns
-------
{
    "task"           : str,
    "draft_type"     : str,
    "max_iterations" : int,
    "iterations"     : [
        {
            "version"  : int,
            "draft"    : str,
            "rationale": str,
            "critique" : dict,   # full critique dict from CriticAgent
        },
        ...
    ],
    "final_draft"    : str,
    "passed"         : bool,
    "total_iterations": int,
    "initial_score"  : int,
    "final_score"    : int,
    "improvement"    : int,   # final_score - initial_score
}
"""

from patterns.p09_generator_critic.generator import GeneratorAgent
from patterns.p09_generator_critic.critic    import CriticAgent

GENERATOR = GeneratorAgent()
CRITIC    = CriticAgent()


def run(task: str, draft_type: str = "Code", max_iterations: int = 4) -> dict:
    """Run the Generator-Critic loop.

    Parameters
    ----------
    task           : The task to generate a draft for.
    draft_type     : "Code" | "Text" | "Plan" | "Email"
    max_iterations : Maximum number of generate-critique cycles.

    Returns
    -------
    See module docstring.
    """
    iterations = []
    previous_draft  = None
    critic_feedback = None

    for i in range(1, max_iterations + 1):
        # ── Generate ──────────────────────────────────────────────────────
        gen_result = GENERATOR.generate(
            task=task,
            draft_type=draft_type,
            iteration=i,
            previous_draft=previous_draft,
            critic_feedback=critic_feedback,
        )
        draft    = gen_result["draft"]
        rationale = gen_result["rationale"]

        # ── Critique ──────────────────────────────────────────────────────
        critique = CRITIC.critique(
            draft=draft,
            task=task,
            draft_type=draft_type,
            iteration=i,
        )

        iterations.append({
            "version":   i,
            "draft":     draft,
            "rationale": rationale,
            "critique":  critique,
        })

        if critique["passed"]:
            break

        # Prepare for next iteration
        previous_draft  = draft
        critic_feedback = critique

    initial_score = iterations[0]["critique"]["overall_score"] if iterations else 0
    final_score   = iterations[-1]["critique"]["overall_score"] if iterations else 0

    return {
        "task":             task,
        "draft_type":       draft_type,
        "max_iterations":   max_iterations,
        "iterations":       iterations,
        "final_draft":      iterations[-1]["draft"] if iterations else "",
        "passed":           iterations[-1]["critique"]["passed"] if iterations else False,
        "total_iterations": len(iterations),
        "initial_score":    initial_score,
        "final_score":      final_score,
        "improvement":      final_score - initial_score,
    }
