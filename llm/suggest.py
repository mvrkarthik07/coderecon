

from collections import defaultdict
from llm.client import run_llm


def build_suggest_prompt(analysis: dict) -> str:
    signals = analysis.get("signals", [])

    # sort by severity
    severity_rank = {"High": 3, "Medium": 2, "Low": 1}
    signals = sorted(
        signals,
        key=lambda s: severity_rank.get(s.get("severity", "Low"), 1),
        reverse=True
    )

    trimmed = signals[:20]

    # 🔥 GROUP SIGNALS BY FUNCTION
    function_risk_map = defaultdict(list)

    for s in trimmed:
        fn = s.get("function")
        if fn:
            function_risk_map[fn].append(s.get("type"))

    # convert to normal dict for prompt readability
    grouped = {k: list(set(v)) for k, v in function_risk_map.items()}

    return f"""
You are a senior engineer generating targeted refactor suggestions.

STRICT RULES:
- Use ONLY the provided signals.
- Do NOT invent metrics.
- Prioritize functions with multiple risk types.
- Reference file path and function name explicitly.

Grouped Risk Signals Per Function:
{grouped}

Raw Signals (Top {len(trimmed)}):
{trimmed}

TASK:

1. Identify highest-risk functions (multiple signal types).
2. Provide concrete refactor strategies.
3. Suggest testing improvements where missing.
4. Provide structural improvements where necessary.
5. Prioritize highest-impact changes.

OUTPUT FORMAT:

## High Risk Functions
## Testing Improvements
## Structural Refactor Suggestions
## Low Priority Improvements

Be precise. No fluff.
"""


def run_suggest_logic(analysis: dict) -> str:
    prompt = build_suggest_prompt(analysis)
    return run_llm(prompt)
