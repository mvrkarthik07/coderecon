import requests
import shutil
import platform
import os


def run_doctor():
    print("[coderecon] Running environment check...\n")

    # 1. Binary Check
    ollama_stat = "✅ Found" if shutil.which("ollama") else "❌ NOT FOUND (Install from ollama.com)"
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Ollama Binary: {ollama_stat}")

    # 2. API Check
    try:
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        resp = requests.get(f"{host}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m['name'] for m in resp.json().get('models', [])]
            print(f"Ollama API: ✅ Reachable at {host}")
            print(f"Models Available: {', '.join(models) if models else 'None'}")

            if 'llama3:latest' not in models and 'llama3' not in models:
                print("⚠️ Warning: 'llama3' model not found. Run 'ollama pull llama3'")
        else:
            print(f"Ollama API: ❌ Error {resp.status_code}")
    except Exception:
        print(f"Ollama API: ❌ NOT REACHABLE. Ensure Ollama is running.")

    print("\n[coderecon] Check complete.")