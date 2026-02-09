import subprocess


def run_llm(prompt: str) -> str:
    """
    Runs a local LLM via Ollama.
    Requires: ollama run llama3
    """
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=prompt,
        text=True,
        capture_output=True,
        errors = "ignore",
        encoding="utf-8",
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout
