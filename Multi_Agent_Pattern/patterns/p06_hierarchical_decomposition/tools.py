"""Worker tools — LLM-powered specialist instruments used by worker agents.

Unlike the deterministic BaseTool used in p04 (Registry & Adapter),
these are LLM-backed tools designed for deep research tasks. Each tool
has a tightly scoped prompt persona that forces a specific kind of output,
giving workers distinct capabilities even though they all call the same
underlying LLM.

Tool roster
-----------
WebResearchTool  — broad information synthesis (background, context, examples)
FactExtractorTool — structured fact/data extraction from a focused topic
DataAnalystTool  — trend analysis, quantitative insights, comparisons
"""

from shared.llm import generate_response


class WebResearchTool:
    """Simulates a deep web-research pass on a specific query.

    Output style: comprehensive prose with context, examples, and key facts.
    Best for: background research, landscape overviews, case studies.
    """

    name = "Web Research"
    icon = "🌐"
    description = (
        "Synthesises broad information on a topic: background, context, "
        "real-world examples, and key findings."
    )

    def run(self, query: str) -> str:
        prompt = (
            "You are a thorough research assistant with access to the entire web. "
            "Research the following topic deeply and return a well-structured report.\n\n"
            f"Research query:\n{query}\n\n"
            "Cover: background & context, current landscape, notable examples or case studies, "
            "key stakeholders, and relevant statistics. "
            "Use markdown with headers and bullet points. Be specific and factual. 300-450 words."
        )
        return generate_response(prompt)


class FactExtractorTool:
    """Extracts and structures key facts, figures, and entities from a topic.

    Output style: numbered facts, data points, named entities.
    Best for: evidence gathering, quick-reference fact sheets.
    """

    name = "Fact Extractor"
    icon = "🔎"
    description = (
        "Extracts and structures key facts, data points, statistics, and "
        "named entities from a specific topic."
    )

    def run(self, query: str) -> str:
        prompt = (
            "You are a precision fact-extraction specialist. "
            "Given a topic, extract and structure the most important verifiable facts.\n\n"
            f"Topic:\n{query}\n\n"
            "Return a structured report with:\n"
            "- **Key Facts** (numbered, specific)\n"
            "- **Important Statistics or Figures**\n"
            "- **Notable Entities** (people, organisations, technologies, dates)\n"
            "- **Common Misconceptions** to avoid (if any)\n\n"
            "Be precise, concise, and bullet-point driven. 200-350 words."
        )
        return generate_response(prompt)


class DataAnalystTool:
    """Analyses trends, patterns, and quantitative dimensions of a topic.

    Output style: trend analysis, metric comparisons, data-driven insights.
    Best for: understanding what is growing/declining, benchmarking.
    """

    name = "Data Analyst"
    icon = "📊"
    description = (
        "Analyses trends, patterns, comparative metrics, and quantitative "
        "insights for a specific topic."
    )

    def run(self, query: str) -> str:
        prompt = (
            "You are a quantitative analyst specialising in trend and pattern analysis. "
            "Analyse the following topic through a data-driven lens.\n\n"
            f"Topic:\n{query}\n\n"
            "Provide:\n"
            "- **Trend Analysis** — what is growing, declining, or shifting?\n"
            "- **Key Metrics & Benchmarks** — quantify wherever possible\n"
            "- **Comparative Analysis** — how does this compare to alternatives?\n"
            "- **Data-Driven Conclusions** — what do the numbers imply?\n\n"
            "Use quantitative reasoning. Where exact numbers are unavailable, "
            "use reasoned estimates with clear assumptions. 200-350 words."
        )
        return generate_response(prompt)


# Ordered tool pool — workers are assigned tools cycling through this list
TOOL_POOL: list = [WebResearchTool(), FactExtractorTool(), DataAnalystTool()]
