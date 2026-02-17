import json
import requests
import shutil
from tqdm import tqdm
import os
# Use a session to keep the connection alive (reuses TCP handshake)
session = requests.Session()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434" )

def run_llm(prompt: str, model: str = "llama3"):
    """
    Direct API implementation with session persistence and optimized streaming.
    """
    if not shutil.which("ollama"):
        return "[coderecon] Skip: Ollama not found."

    url = f"{OLLAMA_HOST}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_ctx": 4096,
            "temperature": 0.1,  # Lowered for even faster/more stable output
            "num_thread": 8,
            "num_predict": 1024,  # Prevent runaway generation
            "low_vram": False
        }
    }

    full_response = []

    try:
        # stream=True with a session is the fastest way to talk to Ollama
        response = session.post(url, json=payload, stream=True, timeout=120)

        # bar_format='{desc}: {elapsed}' gives you a timer without the 0it/s junk
        with tqdm(desc=f"[coderecon] Reasoning with {model}",
                  bar_format='{desc}: {elapsed}',
                  leave=False) as pbar:

            for line in response.iter_lines():
                if not line:
                    continue

                chunk = json.loads(line)
                content = chunk.get("response", "")

                if content:
                    full_response.append(content)
                    # Update the bar every 10 tokens to reduce UI flickering/overhead
                    if len(full_response) % 10 == 0:
                        pbar.update(1)

                if chunk.get("done"):
                    break

        return "".join(full_response).strip()

    except requests.exceptions.Timeout:
        return "[coderecon] Error: LLM Timed out. Context too dense or GPU stalled."
    except Exception as e:
        return f"[coderecon] LLM Error: {str(e)}"