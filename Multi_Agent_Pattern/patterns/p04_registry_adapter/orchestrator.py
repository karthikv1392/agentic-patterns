"""Orchestrator — Registry & Adapter pattern.

The orchestrator is now purely an executor. All decisions (which agents/tools
to use, in what order, with what sub-tasks) are made by the CoordinatorAgent.
The orchestrator simply:

  1. Calls coordinator.coordinate() to get the plan.
  2. Looks up each step in the correct registry (agent or tool).
  3. Invokes each entry through its Adapter with accumulated context.
  4. Synthesises all outputs into a final answer.

Separation of concerns
-----------------------
  CoordinatorAgent  — decides WHAT to do and WHY  (LLM reasoning)
  Orchestrator      — decides HOW to execute       (pure Python control flow)
  Adapter           — bridges interface differences (agent.respond vs tool.run)
"""

from patterns.p04_registry_adapter.registry    import AgentRegistry, ToolRegistry
from patterns.p04_registry_adapter.coordinator import CoordinatorAgent
from patterns.p04_registry_adapter.adapter     import adapter_from_entry
from shared.llm import generate_response


def synthesise(task: str, step_results: list[dict]) -> str:
    """Weave all step outputs into one coherent final answer."""
    contributions = "\n\n".join(
        f"=== {r['name']} ({r['entry_type']}) ===\n{r['output']}"
        for r in step_results
    )
    prompt = (
        "You are a senior editor synthesising outputs from a multi-agent pipeline "
        "into a single, well-structured final answer.\n\n"
        f"Original task:\n{task}\n\n"
        f"Pipeline outputs:\n{contributions}\n\n"
        "Write the final integrated answer. Use clear markdown structure. "
        "Do not concatenate — synthesise: resolve overlaps, fill gaps, and produce "
        "something more coherent than any individual piece."
    )
    return generate_response(prompt)


def orchestrate(
    task:            str,
    coordinator:     CoordinatorAgent,
    agent_registry:  AgentRegistry,
    tool_registry:   ToolRegistry,
) -> dict:
    """Run the full registry-driven pipeline.

    Parameters
    ----------
    task           : user's natural-language task
    coordinator    : the CoordinatorAgent that builds the plan
    agent_registry : registry of LLM-based agents
    tool_registry  : registry of deterministic tools

    Returns
    -------
    {
        "task"                  : str
        "coordinator_reasoning" : str         — coordinator's explanation
        "plan"                  : list[dict]  — [{name, registry, sub_task}]
        "step_results"          : list[dict]  — adapter output per step
        "final_output"          : str         — synthesised answer
    }
    """
    # Step 1 — Coordinator inspects both registries and builds the plan
    coord_output = coordinator.coordinate(task, agent_registry, tool_registry)
    plan         = coord_output["plan"]

    # Step 2 — Execute each step via the correct registry + adapter
    step_results:       list[dict] = []
    context_accumulator: str       = ""

    for step in plan:
        name     = step["name"]
        reg_type = step.get("registry", "agent")

        # Look up in the right registry
        if reg_type == "tool" and name in tool_registry:
            entry = tool_registry.get_entry(name)
        elif name in agent_registry:
            entry = agent_registry.get_entry(name)
        elif name in tool_registry:
            entry = tool_registry.get_entry(name)
        else:
            continue  # unknown name — skip gracefully

        adapter = adapter_from_entry(entry)
        result  = adapter.invoke(step["sub_task"], context=context_accumulator)
        step_results.append(result)
        context_accumulator += f"\n[{result['name']}]:\n{result['output']}\n"

    # Step 3 — Synthesise
    final_output = synthesise(task, step_results)

    return {
        "task":                  task,
        "coordinator_reasoning": coord_output["reasoning"],
        "plan":                  plan,
        "step_results":          step_results,
        "final_output":          final_output,
    }
