import os
from pathlib import Path
from llm.client import run_llm


def run_summary(analysis, repo_root=None):
    print("\n=== Coderecon Summary ===")
    print(f"Files: {len(analysis['files'])}")
    print(f"Functions: {len(analysis['functions'])}")
    print(f"Tests: {len(analysis['tests'])}")

    # 🔍 READ README FOR CONTEXT
    readme_content = ""
    if repo_root:
        readme_path = Path(repo_root) / "README.md"
        if readme_path.exists():
            with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                readme_content = f.read()

    if readme_content:
        print("\n--- Codebase Explanation (via README) ---")
        prompt = f"""
        [ROLE: Lead Architect]
        [CONTEXT: {repo_root}]
        [README CONTENT]
        {readme_content[:3000]} # Truncated to avoid CUDA OOM

        [TASK]
        Summarize the project purpose and explain the folder structure based on this README. 
        Be direct and technical. No fluff. [cite: 2026-02-17]
        """
        explanation = run_llm(prompt)
        print(explanation)