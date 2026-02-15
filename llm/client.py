import shutil
import subprocess

def run_llm(prompt: str, model: str = "llama3"):
    ollama_bin = shutil.which("ollama")

    if not ollama_bin:
        raise RuntimeError(
            "Ollama not found in PATH.\n"
            "Please install Ollama from https://ollama.com and ensure it is in your PATH.\n"
            "Then run: ollama pull llama3"
        )

    result = subprocess.run(
        [ollama_bin, "run", model],
        input=prompt,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout
