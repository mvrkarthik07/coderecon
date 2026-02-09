def build_prompt(file_slice: dict) -> str:
    return f"""
You are a senior software engineer performing a static analysis review.

You are given aggregated analysis signals for ONE file.

File: {file_slice["path"]}
Total signals: {file_slice["signal_count"]}

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
