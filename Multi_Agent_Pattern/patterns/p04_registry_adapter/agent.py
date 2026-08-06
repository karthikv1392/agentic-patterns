"""Registry & Adapter Pattern — entry point.

Wires together both registries, the coordinator, and the orchestrator.

To add a new agent:
  1. Create patterns/p04_registry_adapter/agent_<name>.py
  2. Call AGENT_REGISTRY.register(MyAgent(), description=..., ...)

To add a new tool:
  1. Create patterns/p04_registry_adapter/tool_<name>.py (no LLM allowed)
  2. Call TOOL_REGISTRY.register(MyTool(), description=..., ...)

The coordinator and orchestrator require zero changes.

Agent Registry  (LLM-based reasoning)
--------------------------------------
  🔍 Researcher — deep research, fact-finding, context gathering
  📝 Writer     — drafting, explaining, polished prose
  📊 Analyst    — frameworks, trade-offs, recommendations

Tool Registry  (deterministic — pure Python, no LLM)
------------------------------------------------------
  📊 Text Analyzer — word counts, keywords, readability (pure Python)
  🔢 Calculator    — numeric expression evaluation via Python eval()
"""

from patterns.p04_registry_adapter.agent_researcher  import ResearcherAgent, CAPABILITIES as R_CAPS, BEST_FOR as R_BEST
from patterns.p04_registry_adapter.agent_writer       import WriterAgent,     CAPABILITIES as W_CAPS, BEST_FOR as W_BEST
from patterns.p04_registry_adapter.agent_analyst      import AnalystAgent,    CAPABILITIES as A_CAPS, BEST_FOR as A_BEST
from patterns.p04_registry_adapter.tool_text_analyzer import TextAnalyzerTool, CAPABILITIES as TA_CAPS, BEST_FOR as TA_BEST
from patterns.p04_registry_adapter.tool_calculator    import CalculatorTool,   CAPABILITIES as C_CAPS,  BEST_FOR as C_BEST
from patterns.p04_registry_adapter.registry           import AgentRegistry, ToolRegistry
from patterns.p04_registry_adapter.coordinator        import CoordinatorAgent
from patterns.p04_registry_adapter.orchestrator       import orchestrate

# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------
AGENT_REGISTRY = AgentRegistry()

AGENT_REGISTRY.register(
    ResearcherAgent(),
    description  = "Gathers in-depth background information, facts, examples, and context on any topic.",
    capabilities = R_CAPS,
    best_for     = R_BEST,
)
AGENT_REGISTRY.register(
    WriterAgent(),
    description  = "Transforms information and analysis into clear, well-structured, audience-ready prose.",
    capabilities = W_CAPS,
    best_for     = W_BEST,
)
AGENT_REGISTRY.register(
    AnalystAgent(),
    description  = "Applies analytical frameworks (SWOT, cost-benefit, decision matrix) to produce prioritised recommendations.",
    capabilities = A_CAPS,
    best_for     = A_BEST,
)

# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------
TOOL_REGISTRY = ToolRegistry()

TOOL_REGISTRY.register(
    TextAnalyzerTool(),
    description  = "Deterministic pure-Python text analysis: word counts, vocabulary richness, top keywords by frequency, reading time, Flesch-Kincaid grade. Zero LLM calls.",
    capabilities = TA_CAPS,
    best_for     = TA_BEST,
)
TOOL_REGISTRY.register(
    CalculatorTool(),
    description  = "Extracts and evaluates numeric expressions from text using Python eval(). Deterministic — zero LLM calls.",
    capabilities = C_CAPS,
    best_for     = C_BEST,
)

# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------
COORDINATOR = CoordinatorAgent()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(task: str) -> dict:
    """Run the full registry-driven pipeline for a user task.

    Flow: task → CoordinatorAgent → plan → adapters → synthesise

    Returns
    -------
    {
        "task"                  : str
        "coordinator_reasoning" : str         — coordinator's explanation
        "plan"                  : list[dict]  — [{name, registry, sub_task}]
        "step_results"          : list[dict]  — adapter outputs in order
        "final_output"          : str         — synthesised final answer
    }
    """
    return orchestrate(task, COORDINATOR, AGENT_REGISTRY, TOOL_REGISTRY)
