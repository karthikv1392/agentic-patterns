"""Substitution Layer — pure Python, no LLM.

This is the trust boundary between the Quarantined LLM and the Privileged LLM.

It performs two things deterministically:
  1. Substitution: replaces each symbolic variable (VARn) with its actual value.
  2. Validation: checks every substituted value against known injection patterns.
     Values that match are replaced with a [BLOCKED: reason] sentinel so the
     Privileged LLM can detect them and refuse to proceed.

Why no LLM here?
-----------------
A deterministic regex layer cannot be confused, overridden by clever wording,
or token-manipulated.  It is the hard wall that injection attempts cannot pass.
"""

import re

# ---------------------------------------------------------------------------
# Injection pattern library
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[tuple[str, str]] = [
    # Instruction overrides
    (r"ignore\s+(all\s+)?(previous|prior|the)\s+instructions?",  "instruction override"),
    (r"disregard\s+(all\s+)?(previous|prior|these)\s+",          "instruction disregard"),
    (r"forget\s+(all\s+)?(your|the|previous)\s+instructions?",   "instruction erasure"),
    (r"override\s+(the\s+)?(instructions?|rules?|guidelines?)",   "rule override"),
    (r"new\s+(instruction|directive|rule|command|order)\s*:",     "injected directive"),

    # Persona / role hijacking
    (r"you\s+are\s+now\s+(a\s+|an\s+)?",                        "persona hijacking"),
    (r"act\s+as\s+(if\s+you\s+are|though\s+you\s+are|an?\s+)",  "persona override"),
    (r"pretend\s+(you\s+are|to\s+be)\s+",                        "persona override"),
    (r"from\s+now\s+on\s+(you\s+are|act\s+as|behave)",          "persistent persona override"),

    # System / XML tag injection
    (r"</?(?:system|instructions?|prompt|role|user|assistant|s)\s*/?>", "XML tag injection"),
    (r"\[/?SYSTEM\]|\[/?INST\]|\[/?PROMPT\]",                    "bracket tag injection"),

    # Admin / bypass claims
    (r"admin\s+mode",                                             "admin mode claim"),
    (r"bypass\s+(security|filter|restriction|check|guard)",       "security bypass"),
    (r"jailbreak",                                                "jailbreak keyword"),
    (r"DAN\s+mode|developer\s+mode|god\s+mode",                  "special mode claim"),
    (r"no\s+(restrictions?|limits?|guidelines?|safety)",          "safety removal claim"),

    # Hidden directives
    (r"\[\s*SYSTEM\s+(OVERRIDE|DIRECTIVE|COMMAND)\s*\]",         "system override tag"),
    (r"CONFIDENTIAL\s+INSTRUCTION\s*:",                           "hidden instruction"),
    (r"</?\s*instructions?\s*>",                                  "instruction tag"),
]

_COMPILED = [(re.compile(pat, re.IGNORECASE | re.DOTALL), label)
             for pat, label in _INJECTION_PATTERNS]


def _check_value(value: str) -> list[str]:
    """Return a list of injection pattern labels found in *value*."""
    found = []
    for pattern, label in _COMPILED:
        if pattern.search(value):
            found.append(label)
    return found


def validate_and_substitute(
    param_mapping: dict[str, str],
    variables:     dict[str, str],
) -> dict:
    """Substitute symbolic variables and validate each value.

    Parameters
    ----------
    param_mapping : {param_name: "VARn"} from the Quarantined LLM.
    variables     : {"VARn": actual_value} from the Quarantined LLM.

    Returns
    -------
    {
        "substituted_params"  : dict[str, str]   — param_name -> value (or [BLOCKED:...])
        "validation_results"  : dict[str, dict]  — per-param detail
        "blocked_params"      : list[str]         — param names that were blocked
        "any_blocked"         : bool
        "variable_table"      : list[dict]        — rows for the UI table
    }
    """
    substituted_params: dict[str, dict] = {}
    validation_results: dict[str, dict] = {}
    blocked_params:     list[str]        = []
    variable_table:     list[dict]        = []

    for param, var in param_mapping.items():
        actual_value = variables.get(var, "")
        violations   = _check_value(actual_value)
        is_clean     = len(violations) == 0

        if is_clean:
            final_value = actual_value
            status      = "clean"
        else:
            reason      = " | ".join(violations)
            final_value = f"[BLOCKED: {reason}]"
            status      = "blocked"
            blocked_params.append(param)

        substituted_params[param] = final_value
        validation_results[param] = {
            "variable":   var,
            "raw_value":  actual_value,
            "violations": violations,
            "status":     status,
            "final":      final_value,
        }
        variable_table.append({
            "param":    param,
            "variable": var,
            "value":    actual_value[:120] + ("…" if len(actual_value) > 120 else ""),
            "status":   status,
            "reason":   " | ".join(violations) if violations else "OK",
        })

    return {
        "substituted_params":  substituted_params,
        "validation_results":  validation_results,
        "blocked_params":      blocked_params,
        "any_blocked":         len(blocked_params) > 0,
        "variable_table":      variable_table,
    }
