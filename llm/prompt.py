def build_prompt(file_slice: dict) -> str:
    """
    File-level reasoning: Focus on code-level hazards and specific Rule IDs.
    """
    has_signals = file_slice.get("signal_count", 0) > 0

    return f"""
[CODERECON: FILE-LEVEL DIAGNOSTIC]
TARGET: {file_slice.get("path")}
SIGNALS: {file_slice.get("signal_count")}

### TASK
Analyze the deterministic signals for this file. Rank them by risk.
- **Evidence-Based**: Every risk identified MUST be attributed to a specific Rule ID (e.g., [CR1001]).
- **Fix**: Provide a concrete refactor strategy or code snippet suggestion.

### SIGNALS
{file_slice.get("signals")}

### OUTPUT
1. **Summary**: What is this file's primary risk?
2. **Hazard Analysis**: Grouped by Rule ID. Reference line numbers from the data.
3. **Refactor Suggestion**: One clear path to clean this specific file.
"""


def build_directory_prompt(dir_slice: dict) -> str:
    """
    Directory-level reasoning: Focus on grouping and cross-file patterns.
    """
    return f"""
[CODERECON: DIRECTORY-LEVEL AUDIT]
LOCATION: {dir_slice.get('directory')}
METRICS: {dir_slice.get('file_count')} files | {dir_slice.get('signal_count')} total signals.

### TASK
Identify the 'Theme of Failure' in this directory. 
- **Pattern Recognition**: Identify recurring Rule IDs (e.g., [CR2001]) across multiple files.
- **Prioritization**: Which file in this directory represents the highest architectural risk?

### DATA
{dir_slice.get('signals')}

### OUTPUT
1. **Directory Posture**: Overall health assessment of this module.
2. **Recurring Anti-Patterns**: Identify clusters of signals by Rule ID.
3. **Action Plan**: Prioritized list of files to address.
"""


def build_system_prompt(slice_str: str) -> str:
    """
        Optimized for zero-fluff and rapid token generation.
        """
    return f"""
    [CODERECON: ARCHITECTURAL RECONNAISSANCE]
    ROLE: Cold, pragmatic Lead Architect. [cite: 2026-02-17]
    TONE: Direct, technical, no-bullshit. 

    ### RAW ARCHITECTURAL DATA
    {slice_str}
    ### EMERGENCY PROTOCOL
- IF DATA IS "DATA_NULL" OR EMPTY: Output ONLY: "RECON_REFUSED: No logic detected in target path." and stop. Do not generate headers.
...
    
    ### CONSTRAINTS
    - **Reference Only**: Use ONLY the Rule IDs and files listed above.
    - **Brevity**: Do not use introductory sentences like "Based on the data provided..." 
    - **Mermaid**: Keep the 'graph TD' simple; focus on module relationships, not every single function.

    ### MANDATE
    1. **Flow**: 'graph TD' block of the logic flow.
    2. **Hazards**: Cite Rule IDs (e.g., [CR1001]) for every finding.
    3. **No Hallucinations**: If data is missing, say "Insufficient data for [Area]".

    ### REQUIRED OUTPUT (STRICT)
    ## System Risk Overview
    (2-3 sentences max)

    ## Architectural Hotspots (Mermaid)
    (The graph)

    ## Pattern Analysis
    (Bullet points with Rule IDs)

    ## Top 5 Strategic Fixes
    (Ordered by severity)
    """

def build_github_recon_prompt(slice_str: str, readme_content: str) -> str:
    return f"""
[CODERECON: TRADEMARK RECON]
Analyze this repository and provide a high-clarity summary.

### 📖 README CONTEXT
{readme_content}

### 🏗️ CODE STRUCTURE
{slice_str}

### MANDATE
1. What is this project? Summarize its core purpose.
2. How is it built? Identify the main tech and entry points.
3. Intent vs Reality: Does the code match the README claims?

### OUTPUT FORMAT
## 🚀 Project Identity & Intent
## 🏗️ Architectural Flow
## ⚠️ Implementation Gap
"""