from pathlib import Path
import json
import argparse
import subprocess
from analyzer.scan import run_analysis
import shutil
import tempfile
import time
import os
from report.writer import write_markdown

def safe_delete(path: Path):
    def onerror(func, path_str, exc_info):
        try:
            os.chmod(path_str, 0o777)
            func(path_str)
        except Exception:
            pass

    for _ in range(8):  # more retries
        try:
            shutil.rmtree(path, onerror=onerror)
            return
        except PermissionError:
            time.sleep(0.3)

    print("[coderecon] Warning: Could not fully clean temp directory.")


import re

GITHUB_URL_RE = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/?$"
)

def is_github_url(s: str) -> bool:
    return bool(GITHUB_URL_RE.match(s.strip()))

def clone_repo_temp(url: str) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="coderecon_"))

    print(f"[coderecon] Cloning {url} into temporary directory...")

    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(temp_dir)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return temp_dir



def main():
    parser = argparse.ArgumentParser(
        prog="coderecon",
        description="Deterministic codebase reconnaissance"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)



    #scan command code
    scan = subparsers.add_parser("scan", help="Scan codebase")
    scan.add_argument("path", nargs="?", default=".", help="Path to scan")

    #explain command code
    explain = subparsers.add_parser("explain", help="Explain issues (CLI only)")
    explain.add_argument("path", nargs="?", default=".", help="File, directory, or .")

    #report command code
    report = subparsers.add_parser("report", help="Generate markdown report")
    report.add_argument("path", nargs="?", default=".", help="File, directory, or .")

    #diff command code
    diff = subparsers.add_parser("diff", help="Compare last two scans")

    #summary command code
    summary = subparsers.add_parser("summary", help="Quick repository summary")
    summary.add_argument("path", help="Path to analyze")

    #suggest command code
    suggest = subparsers.add_parser("suggest", help="Generate improvement suggestions")
    suggest.add_argument("path", help="Path to analyze")
    #topo command code
    topo = subparsers.add_parser("topology", help="Topology map + risk heatmap (all files)")
    topo.add_argument("path", help="Local path OR GitHub repo URL")
    topo.add_argument("--max", type=int, default=9999, help="Max files per bucket (default: show all)")

    args = parser.parse_args()

    if args.command == "scan":
        run_analyze(args.path)

    elif args.command == "explain":

        target_path = args.path
        temp_repo = None

        try:
            if is_github_url(target_path):
                temp_repo = clone_repo_temp(target_path)

                # 🔥 analyze in memory only
                analysis = run_analyze(str(temp_repo), write_to_disk=False)

                # 🔥 pass analysis directly
                output = run_explain_logic(str(temp_repo), analysis_data=analysis)
            else:
                output = run_explain_logic(target_path)

            print(output)

        finally:
            if temp_repo and temp_repo.exists():
                print("[coderecon] Cleaning up temporary repository...")
                safe_delete(temp_repo)



    elif args.command == "diff":
        from analyzer.diff import compute_diff
        result = compute_diff()

        if "error" in result:
            print(result["error"])
        else:
            print("[coderecon] Diff Summary")
            print(f"New issues: {result['added_count']}")
            print(f"Resolved issues: {result['removed_count']}")

    elif args.command == "report":

        target_path = args.path
        temp_repo = None

        try:
            if is_github_url(target_path):
                temp_repo = clone_repo_temp(target_path)

                analysis = run_analyze(str(temp_repo), write_to_disk=False)
                output = run_explain_logic(str(temp_repo), analysis_data=analysis)
            else:
                output = run_explain_logic(target_path)

            out = write_markdown(target_path, output)
            print(f"[coderecon] Report written to {out}")

        finally:
            if temp_repo and temp_repo.exists():
                print("[coderecon] Cleaning up temporary repository...")
                safe_delete(temp_repo)
    elif args.command == "summary":
        from report.summary import run_summary
        analysis = run_analyze(args.path, write_to_disk=False)
        run_summary(analysis)

    elif args.command == "suggest":
        from llm.suggest import run_suggest_logic
        analysis = run_analyze(args.path, write_to_disk=False)
        output = run_suggest_logic(analysis)
        print(output)

    elif args.command == "topology":
        from report.topology import generate_topology

        temp_repo = None
        try:
            target_path = args.path

            if is_github_url(args.path):
                temp_repo = clone_repo_temp(args.path)
                target_path = str(temp_repo)

            analysis = run_analyze(target_path, write_to_disk=False)

            text = generate_topology(
                analysis,
                repo_root=target_path,
                max_files_per_bucket=args.max
            )

            print(text)

        finally:
            if temp_repo:
                print("[coderecon] Cleaning up temporary repository...")
                safe_delete(temp_repo)


# noinspection PyTypeChecker
def run_analyze(path: str, write_to_disk: bool = True):
    analysis = run_analysis(path)

    if write_to_disk:
        out = Path(".coderecon")
        out.mkdir(exist_ok=True)

        output_path = out / "analysis.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)

    print("[coderecon] Scan complete")
    print(f"[coderecon] Files scanned: {len(analysis['files'])}")
    print(f"[coderecon] Functions detected: {len(analysis['functions'])}")
    print(f"[coderecon] Tests detected: {len(analysis['tests'])}")
    print(f"[coderecon] Edge cases inferred: {len(analysis['edge_cases'])}")
    print(f"[coderecon] Signals generated: {len(analysis['signals'])}")
    print("[coderecon] Analysis written to .coderecon/analysis.json")
    return analysis

def run_explain_logic(path: str, analysis_data = None) -> str:
    from llm.explain import slice_for_explain, slice_for_explain_data
    from llm.prompt import build_prompt, build_directory_prompt, build_system_prompt
    from llm.client import run_llm

    if analysis_data is not None:
        slice_data = slice_for_explain_data(analysis_data, path)
    else:
        slice_data = slice_for_explain(".coderecon/analysis.json", path)

    if slice_data["mode"] == "system":
        prompt = build_system_prompt(slice_data)
    elif slice_data["mode"] == "directory":
        prompt = build_directory_prompt(slice_data)
    else:
        prompt = build_prompt(slice_data)

    return run_llm(prompt)


if __name__ == "__main__":
    main()
