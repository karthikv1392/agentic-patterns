"""Calculator Tool — Registry & Adapter pattern.

Registry metadata
-----------------
  capabilities : ["calculate", "math", "numbers", "arithmetic", "compute",
                  "percentage", "formula", "evaluate", "expression"]
  best_for     : evaluating numeric expressions, percentage calculations,
                 basic arithmetic, formula evaluation.

Implementation — fully deterministic, zero LLM calls
------------------------------------------------------
Uses Python's built-in math engine to evaluate expressions extracted from the
input string. Steps:

1. Extract all numeric tokens and operator symbols from the task string using regex.
2. Reconstruct candidate expressions (handles %, ^, implicit multiplication).
3. Evaluate using Python eval() inside a restricted sandbox (no builtins, only
   math functions) to prevent code injection.
4. Report all numbers found and any computable expressions.

Because no LLM is involved, the same input always produces the same output.
"""

import re
import math
from collections import namedtuple

from shared.base_tool import BaseTool

CAPABILITIES = [
    "calculate", "math", "numbers", "arithmetic", "compute",
    "percentage", "formula", "evaluate", "expression",
]

BEST_FOR = [
    "evaluating mathematical expressions",
    "computing percentages and ratios",
    "basic arithmetic on numbers found in text",
    "formula evaluation",
]

# Safe evaluation context — only math module functions, no builtins
_SAFE_GLOBALS: dict = {"__builtins__": {}}
_SAFE_GLOBALS.update({k: getattr(math, k) for k in dir(math) if not k.startswith("_")})
_SAFE_GLOBALS.update({"abs": abs, "round": round, "min": min, "max": max})

CalcResult = namedtuple("CalcResult", ["expression", "value", "error"])


def _extract_expressions(text: str) -> list[str]:
    """Pull candidate math expressions out of a natural-language string."""
    # Strip currency symbols, commas in numbers (e.g. $1,000 → 1000)
    cleaned = re.sub(r"[$€£¥]", "", text)
    cleaned = re.sub(r"(\d),(\d)", r"\1\2", cleaned)

    # Replace ^ with ** (power), % with /100 (percentage)
    cleaned = cleaned.replace("^", "**")
    # Replace "X% of Y" → "(X/100)*Y"
    cleaned = re.sub(r"(\d+\.?\d*)\s*%\s*of\s*(\d+\.?\d*)", r"(\1/100)*\2", cleaned)
    # Remaining bare % → /100
    cleaned = re.sub(r"(\d+\.?\d*)\s*%", r"(\1/100)", cleaned)

    # Find substrings that look like math expressions:
    # sequences of digits, operators (+−×÷*/), dots, parens, and spaces
    expr_pattern = re.compile(
        r"(?<!\w)"                        # not preceded by a word char
        r"[\d\.\(]"                       # starts with digit, dot, or open paren
        r"[\d\s\+\-\*\/\.\(\)\*\*]+"     # body: digits, spaces, operators, parens
        r"[\d\.\)]"                       # ends with digit, dot, or close paren
        r"(?!\w)"                         # not followed by a word char
    )
    candidates = [m.group().strip() for m in expr_pattern.finditer(cleaned)]
    # Also look for explicit "= <expr>" or ": <expr>" patterns
    eq_pattern = re.compile(r"[:=]\s*([\d\.\(\)\+\-\*\/\s\*\*]+)")
    for m in eq_pattern.finditer(cleaned):
        candidates.append(m.group(1).strip())

    # Deduplicate and filter trivial single numbers (keep anyway for display)
    seen: set[str] = set()
    result = []
    for c in candidates:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


def _safe_eval(expr: str) -> CalcResult:
    """Evaluate a single expression string safely."""
    try:
        value = eval(expr, _SAFE_GLOBALS, {})  # noqa: S307 — restricted sandbox
        return CalcResult(expr, value, None)
    except Exception as exc:
        return CalcResult(expr, None, str(exc))


class CalculatorTool(BaseTool):

    @property
    def name(self) -> str:
        return "Calculator"

    @property
    def description(self) -> str:
        return (
            "Extracts and evaluates numeric expressions from text using Python's "
            "math engine. Fully deterministic — no LLM involved."
        )

    @property
    def capabilities(self) -> list[str]:
        return CAPABILITIES

    def run(self, task: str) -> str:
        """Parse numeric expressions from *task* and evaluate them deterministically."""
        expressions = _extract_expressions(task)

        # Also extract all raw numbers for summary stats
        raw_numbers = [float(n) for n in re.findall(r"\d+\.?\d*", task)]

        lines: list[str] = ["**Calculator Tool** *(deterministic — Python math engine, no LLM)*\n"]

        if expressions:
            lines.append("**Expressions evaluated:**\n")
            lines.append("| Expression | Result |")
            lines.append("|------------|--------|")
            for expr in expressions:
                res = _safe_eval(expr)
                if res.error:
                    lines.append(f"| `{expr}` | ⚠ {res.error} |")
                else:
                    formatted = (f"{res.value:,.4f}".rstrip("0").rstrip(".")
                                 if isinstance(res.value, float) else str(res.value))
                    lines.append(f"| `{expr}` | **{formatted}** |")
            lines.append("")

        if raw_numbers:
            total   = sum(raw_numbers)
            average = total / len(raw_numbers)
            lines.append("**Numbers found in text:**\n")
            lines.append(f"• Values: {', '.join(str(n) for n in raw_numbers)}")
            lines.append(f"• Count: {len(raw_numbers)}")
            lines.append(f"• Sum: **{total:,.2f}**")
            lines.append(f"• Average: **{average:,.2f}**")
            lines.append(f"• Min: **{min(raw_numbers):,.2f}** | Max: **{max(raw_numbers):,.2f}**")

        if not expressions and not raw_numbers:
            lines.append("No numeric expressions or numbers found in the input.")

        return "\n".join(lines)
