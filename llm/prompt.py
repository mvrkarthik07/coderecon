def build_prompt(file_slice: dict) -> str:
    has_signals = file_slice["signal_count"] > 0

    return f"""
You are a senior software engineer performing a static analysis review.

You are given aggregated analysis signals for ONE file.

File: {file_slice["path"]}
Total signals: {file_slice["signal_count"]}

Task:
{"- Rank issues by severity (High/Medium/Low) with a brief rationale." if has_signals else "- Clearly state that no issues were detected and explan why this file appears clean."}
For each issue:
- explain what it means
- why it matters
- what could go wrong if ignored
- suggest a concrete fix or refactor

Do NOT invent issues.
Do NOT reference data outside this input.

Signals:
{file_slice["signals"]}

Produce a clean Markdown report with:
- Summary
- Issues (grouped logically)
- Recommendations
"""
def build_directory_prompt(dir_slice: dict) -> str:
    return f"""
You are reviewing deterministic static analysis results.

STRICT RULES:
- Use ONLY the provided signals.
- DO NOT invent additional issues.
- DO NOT estimate counts.
- DO NOT assume complexity metrics.
- DO NOT mention tools or concepts not present in signals.
- If signals are limited, say so clearly.

Directory: {dir_slice['directory']}
Files affected: {dir_slice['file_count']}
Total signals: {dir_slice['signal_count']}
Severity breakdown: {dir_slice['severity_counts']}

Signals:
{dir_slice['signals']}

Your task:

1. Summarize the issues strictly based on signals.
2. Group issues by type.
3. Mention specific files and functions.
4. Provide concrete remediation suggestions tied to each signal type.
5. If signals are weak or repetitive, say so.

Be technical, precise, and grounded.

"""
def build_system_prompt(slice_data: dict) -> str:
    return f"""
You are a principal-level software architect conducting a full repository design and risk review.

STRICT RULES:
- Use ONLY the provided structured data.
- Do NOT assume technologies or frameworks not visible in structure.
- Do NOT invent metrics.
- Base all conclusions strictly on counts and signals.
- If signals are weak, state that clearly.

REPOSITORY SUMMARY:
Total files: {slice_data.get("total_files")}
Total functions: {slice_data.get("total_functions")}
Total tests: {slice_data.get("total_tests")}
Test ratio (tests/functions): {slice_data.get("test_ratio")}
Top-level structure: {slice_data.get("top_level_structure")}

RISK SUMMARY:
Total signals: {slice_data.get("total_signals")}
Severity distribution: {slice_data.get("severity_counts", {})}

SAMPLE SIGNALS:
{slice_data.get("signals")}

YOUR TASK:

1. Assess overall system risk posture.
2. Identify architectural hotspots based on signal concentration.
3. Detect recurring structural patterns or anti-patterns.
4. Evaluate testing posture using the test ratio.
5. Rank top 5 highest-leverage fixes.
6. Suggest system-level structural improvements.

OUTPUT FORMAT:

## System Risk Overview
## Architectural Hotspots
## Recurring Patterns
## Testing Posture Analysis
## Top 5 Priority Fixes
## Structural Recommendations

Be technical, precise, and evidence-driven.
"""
