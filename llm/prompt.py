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
You are a senior software engineer reviewing static analysis findings
for a DIRECTORY.

Directory: {dir_slice["directory"]}
Files analyzed: {dir_slice["file_count"]}
Total signals: {dir_slice["signal_count"]}

TASK:
- Identify recurring issue patterns across files.
- Highlight the most risky files or functions.
- Rank concerns by severity (High / Medium / Low).
- Suggest refactors or structural improvements at directory level.

RULES:
- Do not invent issues.
- Base conclusions strictly on provided signals.
- Be concise and technical.
- Use Markdown.

OUTPUT FORMAT:
## Directory Summary
## High-Risk Patterns
## Affected Files
## Recommendations

DATA:
{dir_slice["signals"]}
"""
