"""Multi-Path Plan Generator — single-agent pattern demo.

The user provides a goal. The agent generates a plan where each step contains
2–3 alternative approaches. For each step:

  1. An LLM call evaluates the options and selects the best one (with reasoning).
  2. The agent decides whether the chosen approach requires a tool call.
  3. If a tool is needed, it is invoked and the result is injected as context.
  4. The LLM executes the chosen approach, grounded in the tool result and all
     prior step outputs.

Finally, all step outputs are synthesised into a coherent final answer.

Flow:
    User Goal
        → [LLM] generates plan: each step has 2-3 options  (JSON)
        → for each step:
              [LLM] evaluates options → picks best + reasoning  (JSON)
              [LLM] decides: tool needed? → (optional) tool execution
              [LLM] executes chosen option with tool result + prior context
        → [LLM] synthesises all step outputs → final answer
"""

import json
import re

from tools import TOOL_REGISTRY, execute_tool, tool_descriptions_text
from utils import generate_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict | list:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON found in LLM response:\n{text[:400]}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_multi_path_plan_generator(user_goal: str) -> dict:
    """Run the multi-path plan-generator pipeline.

    Steps:
        1. LLM generates a plan where each step has 2–3 alternative options.
        2. For each step:
               a. LLM evaluates the options and picks the best one.
               b. LLM decides whether a tool is needed for that option.
               c. Tool is executed if required.
               d. LLM produces step output grounded in tool result + prior context.
        3. LLM synthesises all step outputs into a final answer.

    Returns a dict with keys:
        plan_steps    — list of {step_number, goal, options:[{id,approach,description}]}
        evaluations   — list of {step_number, chosen_option_id, approach, rationale}
        step_outputs  — list of {step_number, goal, chosen_approach,
                                  tool_used, tool_output, output}
        final_output  — synthesised final answer
    """

    # ------------------------------------------------------------------
    # Step 1 — Generate multi-path plan
    # ------------------------------------------------------------------
    plan_prompt = (
        "You are an expert planning agent. A user wants to achieve:\n\n"
        f'"{user_goal}"\n\n'
        "Generate a plan with 3–5 steps. For each step, provide 2–3 distinct "
        "alternative approaches the agent could take. Each option should "
        "represent a genuinely different strategy.\n\n"
        "You have access to these tools that steps may later use:\n"
        f"{tool_descriptions_text()}\n\n"
        "Respond with a JSON object and nothing else:\n"
        "```json\n"
        "{\n"
        '  "steps": [\n'
        "    {\n"
        '      "step_number": 1,\n'
        '      "goal": "<what this step accomplishes>",\n'
        '      "options": [\n'
        '        {"id": "A", "approach": "<short name>", "description": "<how this works>"},\n'
        '        {"id": "B", "approach": "<short name>", "description": "<how this works>"},\n'
        '        {"id": "C", "approach": "<short name>", "description": "<how this works>"}\n'
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "```"
    )
    raw_plan = generate_response(plan_prompt)

    try:
        plan_steps = _extract_json(raw_plan).get("steps", [])
        if not plan_steps:
            raise ValueError("empty")
    except Exception:
        plan_steps = [{
            "step_number": 1,
            "goal": "Execute the goal",
            "options": [{"id": "A", "approach": "Direct", "description": raw_plan}],
        }]

    # ------------------------------------------------------------------
    # Steps 2a–2d — Evaluate, decide tool, execute each step
    # ------------------------------------------------------------------
    evaluations: list[dict] = []
    step_outputs: list[dict] = []
    accumulated_context = ""

    for step in plan_steps:
        step_num = step.get("step_number", len(step_outputs) + 1)
        step_goal = step.get("goal", "")
        options = step.get("options", [])
        context_block = (
            f"\n\nContext from completed steps:\n{accumulated_context}"
            if accumulated_context else ""
        )

        options_text = "\n".join(
            f"  Option {o['id']}: {o['approach']} — {o['description']}"
            for o in options
        )

        # -- 2a. Evaluate options --
        eval_prompt = (
            "You are an expert decision-making agent.\n\n"
            f"Overall goal: \"{user_goal}\"\n"
            f"Current step ({step_num}): {step_goal}"
            f"{context_block}\n\n"
            "Options for this step:\n"
            f"{options_text}\n\n"
            "Evaluate each option for effectiveness, feasibility, and fit with "
            "prior context. Select the single best option.\n\n"
            "Respond with a JSON object and nothing else:\n"
            "```json\n"
            "{\n"
            '  "chosen_option_id": "<A, B, or C>",\n'
            '  "chosen_approach": "<approach name>",\n'
            '  "rationale": "<why this is the best choice>"\n'
            "}\n"
            "```"
        )
        raw_eval = generate_response(eval_prompt)

        try:
            ev = _extract_json(raw_eval)
            chosen_id = ev.get("chosen_option_id", options[0]["id"] if options else "A")
            chosen_approach = ev.get("chosen_approach", "")
            rationale = ev.get("rationale", "")
        except Exception:
            chosen_id = options[0]["id"] if options else "A"
            chosen_approach = options[0].get("approach", "") if options else ""
            rationale = raw_eval

        evaluations.append({
            "step_number": step_num,
            "chosen_option_id": chosen_id,
            "approach": chosen_approach,
            "rationale": rationale,
        })

        chosen_desc = next(
            (o["description"] for o in options if o["id"] == chosen_id),
            chosen_approach,
        )

        # -- 2b. Tool decision --
        tool_decision_prompt = (
            "You are an expert agent deciding whether to use a tool for a step.\n\n"
            f"Overall goal: \"{user_goal}\"\n"
            f"Step ({step_num}): {step_goal}\n"
            f"Chosen approach: {chosen_approach} — {chosen_desc}"
            f"{context_block}\n\n"
            "Available tools:\n"
            f"{tool_descriptions_text()}\n\n"
            "Decide: does this step benefit from calling one of the above tools? "
            "If yes, specify the tool and exact parameters. "
            "If no tool is needed, set needs_tool to false.\n\n"
            "Respond with a JSON object and nothing else:\n"
            "```json\n"
            "{\n"
            '  "needs_tool": true or false,\n'
            '  "tool_name": "<tool name or null>",\n'
            '  "parameters": {<parameters or {}>},\n'
            '  "reasoning": "<brief explanation>"\n'
            "}\n"
            "```"
        )
        raw_tool_decision = generate_response(tool_decision_prompt)

        tool_used = None
        tool_output = None
        try:
            td = _extract_json(raw_tool_decision)
            if td.get("needs_tool") and td.get("tool_name") in TOOL_REGISTRY:
                tool_used = td["tool_name"]
                tool_output = execute_tool(tool_used, td.get("parameters", {}))
        except Exception:
            pass

        # -- 2c. Execute step --
        tool_block = (
            f"\n\nTool used: {tool_used}\nTool output:\n```\n{tool_output}\n```"
            if tool_output else ""
        )
        exec_prompt = (
            "You are an expert assistant executing one step in a plan.\n\n"
            f"Overall goal: \"{user_goal}\"\n"
            f"Step {step_num}: {step_goal}\n"
            f"Approach: {chosen_approach} — {chosen_desc}"
            f"{context_block}"
            f"{tool_block}\n\n"
            "Produce a detailed, well-structured output for this step. "
            "If a tool result is provided, incorporate it directly. "
            "Use markdown formatting."
        )
        output = generate_response(exec_prompt)

        step_outputs.append({
            "step_number": step_num,
            "goal": step_goal,
            "chosen_approach": chosen_approach,
            "tool_used": tool_used,
            "tool_output": tool_output,
            "output": output,
        })
        accumulated_context += (
            f"\nStep {step_num} ({step_goal}) [approach: {chosen_approach}]"
            + (f" [tool: {tool_used}]" if tool_used else "")
            + f":\n{output}\n"
        )

    # ------------------------------------------------------------------
    # Step 3 — Synthesise final answer
    # ------------------------------------------------------------------
    steps_summary = "\n\n".join(
        f"**Step {s['step_number']}: {s['goal']}** *(approach: {s['chosen_approach']})*\n{s['output']}"
        for s in step_outputs
    )
    synthesis_prompt = (
        "You are an expert assistant. A user had the following goal:\n\n"
        f'"{user_goal}"\n\n'
        "A multi-path planning agent evaluated options at each step and "
        "executed the best approach (using tools where needed). Results:\n\n"
        f"{steps_summary}\n\n"
        "Synthesise all of the above into a single, coherent, comprehensive "
        "final answer. Integrate the outputs naturally — do not repeat verbatim. "
        "Use markdown formatting."
    )
    final_output = generate_response(synthesis_prompt)

    return {
        "plan_steps": plan_steps,
        "evaluations": evaluations,
        "step_outputs": step_outputs,
        "final_output": final_output,
    }


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    default_goal = "Design a marketing strategy for a new mobile productivity app"
    print(f"Running Multi-Path Plan Generator:\n  {default_goal!r}\n")

    result = run_multi_path_plan_generator(default_goal)

    print("=" * 60)
    print("MULTI-PATH PLAN")
    print("=" * 60)
    for step in result["plan_steps"]:
        print(f"\nStep {step['step_number']}: {step['goal']}")
        for opt in step.get("options", []):
            print(f"  [{opt['id']}] {opt['approach']}: {opt['description']}")

    print()
    print("=" * 60)
    print("EVALUATIONS")
    print("=" * 60)
    for ev in result["evaluations"]:
        print(f"Step {ev['step_number']}: chose {ev['chosen_option_id']} — {ev['approach']}")
        print(f"  Rationale: {ev['rationale']}")

    print()
    for s in result["step_outputs"]:
        print("=" * 60)
        print(f"STEP {s['step_number']} [{s['chosen_approach']}]"
              + (f" — tool: {s['tool_used']}" if s['tool_used'] else ""))
        print("=" * 60)
        print(s["output"])
        print()

    print("=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(result["final_output"])
