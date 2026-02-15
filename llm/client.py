import subprocess
import shutil

def run_llm(prompt: str, model: str = "llama3"):
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        raise RuntimeError("Ollama not found in PATH")

    result = subprocess.run(
        [ollama_bin, "run", model],
        input=prompt.encode("utf-8"),
        capture_output=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="ignore"))

    return result.stdout.decode("utf-8", errors="ignore")
