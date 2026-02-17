import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import re
import requests

# Core Imports
from analyzer.scan import run_analysis
from report.writer import write_markdown

# -----------------------------------------------------------------------------
# UTILS & GITHUB HANDLING
# -----------------------------------------------------------------------------

GITHUB_URL_RE = re.compile(r"^https://github\.com/[^/]+/[^/]+/?$")


def is_github_url(s: str) -> bool:
    return bool(GITHUB_URL_RE.match(s.strip()))


def safe_delete(path: Path):
    """Retries deletion to handle Windows file locks."""

    def onerror(func, path_str, exc_info):
        try:
            os.chmod(path_str, 0o777)
            func(path_str)
        except Exception:
            pass

    for _ in range(8):
        try:
            if path.exists():
                shutil.rmtree(path, onerror=onerror)
            return
        except PermissionError:
            time.sleep(0.3)
    print(f"[coderecon] Warning: Could not clean {path}")


def clone_repo_temp(url: str) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="coderecon_"))
    print(f"[coderecon] Cloning {url} into ephemeral storage...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(temp_dir)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git clone failed: {result.stderr}")
    return temp_dir


# -----------------------------------------------------------------------------
# CORE LOGIC WRAPPERS
# -----------------------------------------------------------------------------
def display_detailed_help():
    """Prints a custom, formatted guide to CodeRecon commands."""
    help_text = """
🔍 CodeRecon Detailed Command Guide

CORE ANALYSIS:
  explain [PATH]   LLM-powered logic breakdown. Explains the 'intent' of the code.
  topology [PATH]  Maps architecture and identifies functional 'buckets' (Core, Entry, etc.).
  report [PATH]    Generates a formal RECON_REPORT.md with Mermaid diagrams.
  scan [PATH]      High-speed AST structural scan (no LLM reasoning).

INTELLIGENCE:
  summary [PATH]   Provides a high-level executive summary of the repository's purpose.
  suggest [PATH]   Analyzes the codebase for implementation gaps and architectural risks.

SYSTEM & UTILS:
  doctor           Checks system health, Ollama status, and dependency alignment.
  clean            Wipes ephemeral clones and local cache files.
  help             Displays this detailed guide.

USAGE EXAMPLES:
  $ coderecon explain .
  $ coderecon suggest ./src
  $ coderecon report https://github.com/mvrkarthik07/coderecon
    """
    print(help_text)


def get_analysis_data(path: str, force_scan: bool = False) -> dict:
    """
    Prioritizes existing analysis.json.
    Only scans if file is missing or force_scan is True.
    """
    analysis_file = Path("analysis.json")

    if not force_scan and analysis_file.exists():
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # CHECK: Does the cached data match the path we are looking at?
            cached_root = data.get("root", "")
            # Normalize paths to compare them properly
            if os.path.abspath(cached_root) == os.path.abspath(path):
                print(f"[coderecon] Using existing analysis.json...")
                return data
            else:
                print(f"[coderecon] Cache mismatch (Target changed). Re-scanning...")
        except Exception:
            print(f"[coderecon] analysis.json is corrupt. Re-scanning...")

    # Fallback: Run the full scan
    print(f"[coderecon] Scanning '{path}'...")
    analysis = run_analysis(path)
    # Store the root in the JSON so we can verify it later
    analysis["root"] = str(Path(path).absolute())

    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=4)

    return analysis


def run_explain_logic(path: str, analysis_data: dict) -> str:
    from llm.explain import slice_for_explain_data
    from llm.prompt import build_system_prompt, build_github_recon_prompt
    from llm.client import run_llm

    # Extract README
    readme_path = Path(path) / "README.md"
    readme_content = ""
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
            readme_content = f.read()[:5000]

    slice_str = slice_for_explain_data(analysis_data, path)
    signals = analysis_data.get("signals", [])

    # The "It worked before" logic:
    # If there's a README, use the Recon prompt regardless of minor signals.
    if readme_content:
        prompt = build_github_recon_prompt(slice_str, readme_content)
    else:
        prompt = build_system_prompt(slice_str)

    return run_llm(prompt)


def run_clean_logic():
    """Wipes the local cache files."""
    files_to_clean = ["analysis.json", ".coderecon/cache.json"]
    cleaned = False
    for f in files_to_clean:
        p = Path(f)
        if p.exists():
            p.unlink()
            print(f"[coderecon] Removed {f}")
            cleaned = True
    if not cleaned:
        print("[coderecon] No cache found to clean.")


def run_doctor():
    """Diagnostic suite to verify environment health."""
    print(f"\n{'=' * 40}")
    print("      CODERECON SYSTEM DIAGNOSTICS")
    print(f"{'=' * 40}\n")

    print(f"[SYSTEM] OS: {platform.system()} {platform.release()}")
    print(f"[SYSTEM] Python: {sys.version.split()[0]}")

    ollama_path = shutil.which("ollama")
    if ollama_path:
        print(f"[BINARY] Ollama: ✅ Found at {ollama_path}")
    else:
        print(f"[BINARY] Ollama: ❌ NOT FOUND.")

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        resp = requests.get(f"{host}/api/tags", timeout=3)
        if resp.status_code == 200:
            print(f"[API]    Service: ✅ Reachable at {host}")
            models = [m['name'] for m in resp.json().get('models', [])]
            if any("llama3" in m for m in models):
                print(f"[MODELS] Llama3:  ✅ Installed")
            else:
                print(f"[MODELS] Llama3:  ❌ NOT FOUND. Run 'ollama pull llama3'")
    except Exception:
        print(f"[API]    Service: ❌ NOT REACHABLE.")

    try:
        test_file = "test_perm.tmp"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print(f"[FILES]  Perms:   ✅ Write Access OK")
    except Exception:
        print(f"[FILES]  Perms:   ❌ WRITE ACCESS DENIED")

    print(f"\n{'=' * 40}\n")


# -----------------------------------------------------------------------------
# MAIN CLI ENTRY
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="coderecon", description="Engineering-first reconnaissance")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register Commands
    subparsers.add_parser("doctor")
    subparsers.add_parser("clean")
    subparsers.add_parser("help")


    for cmd in ["scan", "explain", "report", "summary", "suggest", "topology"]:
        p = subparsers.add_parser(cmd)
        p.add_argument("path", nargs="?", default=".")
        if cmd == "topology":
            p.add_argument("--max", type=int, default=9999)

    args = parser.parse_args()

    if args.command == "doctor":
        run_doctor()
        return
    if args.command == "help":
        display_detailed_help()
        return
    if args.command == "clean":
        run_clean_logic()
        return

    target_path = args.path
    temp_repo = None

    try:
        # 1. Resolve Active Path (Remote Clone vs Local)
        if is_github_url(target_path):
            temp_repo = clone_repo_temp(target_path)
            active_path = str(temp_repo)
            # Scanned in-memory for remote repos to avoid saving remote trash to local root
            analysis = run_analysis(active_path)
        else:
            active_path = target_path
            force = (args.command == "scan")
            analysis = get_analysis_data(active_path, force_scan=force)

        # 2. Execute Dispatch
        if args.command == "scan":
            print(f"[coderecon] Scan complete: {len(analysis['files'])} files.")

        elif args.command == "explain":
            # Pass the actual directory (temp or local) and the analyzed data
            result = run_explain_logic(active_path, analysis)
            print(result)

        elif args.command == "report":
            # Filter out noisy 'untested' signals for the formal report
            analysis['signals'] = [s for s in analysis.get('signals', []) if s.get('type') != 'untested']

            explanation = run_explain_logic(active_path, analysis)
            out = write_markdown(target_path, explanation, analysis)
            print(f"✅ [coderecon] Formal report generated: {out}")

        elif args.command == "summary":
            from report.summary import run_summary
            run_summary(analysis, repo_root=active_path)

        elif args.command == "suggest":
            from llm.suggest import run_suggest_logic
            print(run_suggest_logic(analysis))



        elif args.command == "topology":
            from report.topology import generate_topology
            print(generate_topology(analysis, repo_root=active_path, max_files_per_bucket=args.max))

    finally:
        if temp_repo:
            print("[coderecon] Cleaning ephemeral storage...")
            safe_delete(temp_repo)


if __name__ == "__main__":
    main()